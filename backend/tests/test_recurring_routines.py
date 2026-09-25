"""
Tests for recurring routines: create, list, partial update (the
is_active pause/resume toggle), delete, and validation.
"""
import json
import uuid
from base64 import b64encode

import itsdangerous
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import Base, engine, SessionLocal
from app.main import app
from app.models.activity import Activity
from app.models.user import User

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clear_cookies_between_tests():
    client.cookies.clear()
    yield
    client.cookies.clear()


def _cookie_for(user_id: str) -> dict:
    signer = itsdangerous.TimestampSigner(settings.SESSION_SECRET)
    data = b64encode(json.dumps({"user_id": user_id}).encode("utf-8"))
    return {settings.SESSION_COOKIE_NAME: signer.sign(data).decode("utf-8")}


@pytest.fixture
def test_user_with_activity():
    db = SessionLocal()
    user = User(
        linkedin_sub=f"test-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        first_name="Test",
        last_name="User",
    )
    activity = Activity(id=uuid.uuid4(), name=f"Test Activity {uuid.uuid4()}", category="sports")
    db.add(user)
    db.add(activity)
    db.commit()
    db.refresh(user)
    db.refresh(activity)
    yield {"user": user, "activity_id": str(activity.id)}
    db.close()


def test_routines_requires_auth():
    assert client.get("/api/profile/routines").status_code == 401
    assert client.post("/api/profile/routines", json={"activity_id": str(uuid.uuid4())}).status_code == 401


def test_add_and_list_routine(test_user_with_activity):
    ctx = test_user_with_activity
    cookies = _cookie_for(str(ctx["user"].id))
    response = client.post(
        "/api/profile/routines",
        json={
            "activity_id": ctx["activity_id"],
            "days_of_week": ["tuesday", "thursday"],
            "time_window": "evening",
            "location_context": "Central Park",
            "visible_on_profile": True,
        },
        cookies=cookies,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["days_of_week"] == ["tuesday", "thursday"]
    assert body["is_active"] is True

    listing = client.get("/api/profile/routines", cookies=cookies).json()
    assert len(listing) == 1


def test_invalid_day_rejected(test_user_with_activity):
    ctx = test_user_with_activity
    cookies = _cookie_for(str(ctx["user"].id))
    response = client.post(
        "/api/profile/routines",
        json={"activity_id": ctx["activity_id"], "days_of_week": ["someday"]},
        cookies=cookies,
    )
    assert response.status_code == 422


def test_invalid_activity_id_rejected(test_user_with_activity):
    ctx = test_user_with_activity
    cookies = _cookie_for(str(ctx["user"].id))
    response = client.post(
        "/api/profile/routines",
        json={"activity_id": str(uuid.uuid4())},
        cookies=cookies,
    )
    assert response.status_code == 400


def test_patch_pause_only_changes_is_active(test_user_with_activity):
    """The partial-update PATCH should only touch fields explicitly
    sent, not silently reset everything else - this is the whole point
    of using exclude_unset rather than a full replace."""
    ctx = test_user_with_activity
    cookies = _cookie_for(str(ctx["user"].id))
    create_resp = client.post(
        "/api/profile/routines",
        json={
            "activity_id": ctx["activity_id"],
            "days_of_week": ["monday"],
            "time_window": "morning",
            "location_context": "my gym",
        },
        cookies=cookies,
    )
    routine_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/profile/routines/{routine_id}", json={"is_active": False}, cookies=cookies
    )
    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert body["is_active"] is False
    assert body["days_of_week"] == ["monday"]
    assert body["time_window"] == "morning"
    assert body["location_context"] == "my gym"


def test_delete_routine(test_user_with_activity):
    ctx = test_user_with_activity
    cookies = _cookie_for(str(ctx["user"].id))
    create_resp = client.post(
        "/api/profile/routines", json={"activity_id": ctx["activity_id"]}, cookies=cookies
    )
    routine_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/profile/routines/{routine_id}", cookies=cookies)
    assert delete_resp.status_code == 204
    listing = client.get("/api/profile/routines", cookies=cookies).json()
    assert len(listing) == 0


def test_routine_scoped_to_owner(test_user_with_activity):
    ctx = test_user_with_activity
    cookies = _cookie_for(str(ctx["user"].id))

    other_db = SessionLocal()
    other_user = User(
        linkedin_sub=f"test-other-routine-{uuid.uuid4()}",
        email=f"test-other-routine-{uuid.uuid4()}@example.com",
        first_name="Other",
        last_name="User",
    )
    other_db.add(other_user)
    other_db.commit()
    other_db.refresh(other_user)
    other_cookies = _cookie_for(str(other_user.id))

    create_resp = client.post(
        "/api/profile/routines", json={"activity_id": ctx["activity_id"]}, cookies=other_cookies
    )
    other_routine_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/profile/routines/{other_routine_id}", cookies=cookies)
    assert delete_resp.status_code == 404

    patch_resp = client.patch(
        f"/api/profile/routines/{other_routine_id}", json={"is_active": False}, cookies=cookies
    )
    assert patch_resp.status_code == 404

    still_there = client.get("/api/profile/routines", cookies=other_cookies).json()
    assert any(r["id"] == other_routine_id for r in still_there)

    other_db.close()
