"""
Tests for the additional profile photos feature: upload, list, delete,
and the "must be a loved activity/interest" tagging validation.
"""
import io
import json
import shutil
import uuid
from base64 import b64encode
from pathlib import Path

import itsdangerous
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import settings
from app.db.session import Base, engine, SessionLocal
from app.main import app
from app.models.activity import Activity, UserActivity
from app.models.interest import Interest, UserInterest
from app.models.user import User
from app.services.photo_storage import UPLOADS_DIR

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Real files get written to disk during these tests - clean up so
    # they don't accumulate in the sandbox across test runs.
    if UPLOADS_DIR.exists():
        shutil.rmtree(UPLOADS_DIR)


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
def test_user_with_loved_activity_and_interest():
    db = SessionLocal()
    user = User(
        linkedin_sub=f"test-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        first_name="Test",
        last_name="User",
    )
    db.add(user)

    loved_activity = Activity(id=uuid.uuid4(), name=f"Loved Activity {uuid.uuid4()}", category="sports")
    not_loved_activity = Activity(id=uuid.uuid4(), name=f"Not Loved Activity {uuid.uuid4()}", category="sports")
    loved_interest = Interest(id=uuid.uuid4(), name=f"Loved Interest {uuid.uuid4()}")
    db.add_all([loved_activity, not_loved_activity, loved_interest])
    db.commit()
    db.refresh(user)

    db.add(UserActivity(user_id=user.id, activity_id=loved_activity.id, is_top_pick=True))
    db.add(UserActivity(user_id=user.id, activity_id=not_loved_activity.id, is_top_pick=False))
    db.add(UserInterest(user_id=user.id, interest_id=loved_interest.id, is_top_pick=True))
    db.commit()

    yield {
        "user": user,
        "loved_activity_id": str(loved_activity.id),
        "not_loved_activity_id": str(not_loved_activity.id),
        "loved_interest_id": str(loved_interest.id),
    }
    db.close()


def _test_image_bytes() -> bytes:
    img = Image.new("RGB", (50, 50), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_photos_requires_auth():
    assert client.get("/api/profile/photos").status_code == 401


def test_upload_untagged_photo(test_user_with_loved_activity_and_interest):
    ctx = test_user_with_loved_activity_and_interest
    cookies = _cookie_for(str(ctx["user"].id))
    response = client.post(
        "/api/profile/photos",
        files={"file": ("test.jpg", _test_image_bytes(), "image/jpeg")},
        cookies=cookies,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["tagged_activity_id"] is None
    assert body["url"].startswith("/api/uploads/photos/")


def test_upload_photo_tagged_to_loved_activity(test_user_with_loved_activity_and_interest):
    ctx = test_user_with_loved_activity_and_interest
    cookies = _cookie_for(str(ctx["user"].id))
    response = client.post(
        "/api/profile/photos",
        files={"file": ("test.jpg", _test_image_bytes(), "image/jpeg")},
        data={"tagged_activity_id": ctx["loved_activity_id"]},
        cookies=cookies,
    )
    assert response.status_code == 201
    assert response.json()["tagged_activity_id"] == ctx["loved_activity_id"]


def test_upload_photo_tagged_to_non_loved_activity_rejected(test_user_with_loved_activity_and_interest):
    ctx = test_user_with_loved_activity_and_interest
    cookies = _cookie_for(str(ctx["user"].id))
    response = client.post(
        "/api/profile/photos",
        files={"file": ("test.jpg", _test_image_bytes(), "image/jpeg")},
        data={"tagged_activity_id": ctx["not_loved_activity_id"]},
        cookies=cookies,
    )
    assert response.status_code == 400


def test_upload_photo_tagged_to_loved_interest(test_user_with_loved_activity_and_interest):
    ctx = test_user_with_loved_activity_and_interest
    cookies = _cookie_for(str(ctx["user"].id))
    response = client.post(
        "/api/profile/photos",
        files={"file": ("test.jpg", _test_image_bytes(), "image/jpeg")},
        data={"tagged_interest_id": ctx["loved_interest_id"]},
        cookies=cookies,
    )
    assert response.status_code == 201
    assert response.json()["tagged_interest_name"] is not None


def test_upload_rejects_invalid_image(test_user_with_loved_activity_and_interest):
    ctx = test_user_with_loved_activity_and_interest
    cookies = _cookie_for(str(ctx["user"].id))
    response = client.post(
        "/api/profile/photos",
        files={"file": ("test.jpg", b"this is not an image, just garbage bytes", "image/jpeg")},
        cookies=cookies,
    )
    assert response.status_code == 400


def test_max_four_photos_enforced(test_user_with_loved_activity_and_interest):
    ctx = test_user_with_loved_activity_and_interest
    cookies = _cookie_for(str(ctx["user"].id))
    for _ in range(4):
        response = client.post(
            "/api/profile/photos",
            files={"file": ("test.jpg", _test_image_bytes(), "image/jpeg")},
            cookies=cookies,
        )
        assert response.status_code == 201

    fifth = client.post(
        "/api/profile/photos",
        files={"file": ("test.jpg", _test_image_bytes(), "image/jpeg")},
        cookies=cookies,
    )
    assert fifth.status_code == 400


def test_delete_photo_removes_file_from_disk(test_user_with_loved_activity_and_interest):
    ctx = test_user_with_loved_activity_and_interest
    cookies = _cookie_for(str(ctx["user"].id))
    upload_response = client.post(
        "/api/profile/photos",
        files={"file": ("test.jpg", _test_image_bytes(), "image/jpeg")},
        cookies=cookies,
    )
    photo_id = upload_response.json()["id"]
    relative_path = upload_response.json()["url"].replace("/api/uploads/", "")
    full_path = UPLOADS_DIR.parent / relative_path
    assert full_path.exists(), "file should exist on disk right after upload"

    delete_response = client.delete(f"/api/profile/photos/{photo_id}", cookies=cookies)
    assert delete_response.status_code == 204
    assert not full_path.exists(), "file should be gone from disk after delete, not just the DB row"


def test_photo_delete_scoped_to_owner(test_user_with_loved_activity_and_interest):
    ctx = test_user_with_loved_activity_and_interest
    cookies = _cookie_for(str(ctx["user"].id))

    other_db = SessionLocal()
    other_user = User(
        linkedin_sub=f"test-other-photo-{uuid.uuid4()}",
        email=f"test-other-photo-{uuid.uuid4()}@example.com",
        first_name="Other",
        last_name="User",
    )
    other_db.add(other_user)
    other_db.commit()
    other_db.refresh(other_user)
    other_cookies = _cookie_for(str(other_user.id))

    upload_response = client.post(
        "/api/profile/photos",
        files={"file": ("test.jpg", _test_image_bytes(), "image/jpeg")},
        cookies=other_cookies,
    )
    other_photo_id = upload_response.json()["id"]

    delete_response = client.delete(f"/api/profile/photos/{other_photo_id}", cookies=cookies)
    assert delete_response.status_code == 404

    still_there = client.get("/api/profile/photos", cookies=other_cookies).json()
    assert any(p["id"] == other_photo_id for p in still_there)

    other_db.close()
