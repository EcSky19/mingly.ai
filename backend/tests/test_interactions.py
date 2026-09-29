"""
Tests for the interaction-tracking foundation: record, reconsider
(upsert), self-interaction and invalid-target rejection, ownership
scoping.
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
def two_users():
    db = SessionLocal()
    a = User(linkedin_sub=f"test-{uuid.uuid4()}", email=f"test-{uuid.uuid4()}@example.com", first_name="A", last_name="User")
    b = User(linkedin_sub=f"test-{uuid.uuid4()}", email=f"test-{uuid.uuid4()}@example.com", first_name="B", last_name="User")
    db.add_all([a, b])
    db.commit()
    db.refresh(a)
    db.refresh(b)
    yield {"a": a, "b": b}
    db.close()


def test_interact_requires_auth():
    assert client.post("/api/discover/interact", json={"target_user_id": str(uuid.uuid4()), "action": "dismissed"}).status_code == 401
    assert client.get("/api/discover/interactions").status_code == 401


def test_record_dismissal(two_users):
    cookies = _cookie_for(str(two_users["a"].id))
    response = client.post(
        "/api/discover/interact",
        json={"target_user_id": str(two_users["b"].id), "action": "dismissed"},
        cookies=cookies,
    )
    assert response.status_code == 201
    assert response.json()["action"] == "dismissed"


def test_reconsidering_updates_same_row_not_duplicate(two_users):
    """The core design point: dismissing then later marking interested
    should update the existing row (same id), not create a second one -
    that's what the unique constraint and upsert logic are for."""
    cookies = _cookie_for(str(two_users["a"].id))
    first = client.post(
        "/api/discover/interact",
        json={"target_user_id": str(two_users["b"].id), "action": "dismissed"},
        cookies=cookies,
    ).json()

    second = client.post(
        "/api/discover/interact",
        json={"target_user_id": str(two_users["b"].id), "action": "interested"},
        cookies=cookies,
    ).json()

    assert second["id"] == first["id"]
    assert second["action"] == "interested"

    listing = client.get("/api/discover/interactions", cookies=cookies).json()
    assert len(listing) == 1


def test_self_interaction_rejected(two_users):
    cookies = _cookie_for(str(two_users["a"].id))
    response = client.post(
        "/api/discover/interact",
        json={"target_user_id": str(two_users["a"].id), "action": "interested"},
        cookies=cookies,
    )
    assert response.status_code == 400


def test_invalid_target_rejected(two_users):
    cookies = _cookie_for(str(two_users["a"].id))
    response = client.post(
        "/api/discover/interact",
        json={"target_user_id": str(uuid.uuid4()), "action": "interested"},
        cookies=cookies,
    )
    assert response.status_code == 400


def test_interactions_scoped_to_owner(two_users):
    """A's interactions list should never include what B recorded."""
    cookies_a = _cookie_for(str(two_users["a"].id))
    cookies_b = _cookie_for(str(two_users["b"].id))

    client.post(
        "/api/discover/interact",
        json={"target_user_id": str(two_users["b"].id), "action": "interested"},
        cookies=cookies_a,
    )

    third_db = SessionLocal()
    c = User(linkedin_sub=f"test-{uuid.uuid4()}", email=f"test-{uuid.uuid4()}@example.com", first_name="C", last_name="User")
    third_db.add(c)
    third_db.commit()
    third_db.refresh(c)

    client.post(
        "/api/discover/interact",
        json={"target_user_id": str(c.id), "action": "dismissed"},
        cookies=cookies_b,
    )

    listing_a = client.get("/api/discover/interactions", cookies=cookies_a).json()
    listing_b = client.get("/api/discover/interactions", cookies=cookies_b).json()

    assert len(listing_a) == 1
    assert len(listing_b) == 1
    assert listing_a[0]["target_user_id"] != listing_b[0]["target_user_id"]

    third_db.close()
