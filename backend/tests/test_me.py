"""
Tests for /api/auth/me's profile_photo_url. The stored value is normally
a relative path to our own saved copy of the LinkedIn photo, but rows
written before that change still hold LinkedIn's full (expiring) URL
until the person next logs in - both shapes must produce a usable URL.
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


def _make_user(photo):
    db = SessionLocal()
    user = User(
        linkedin_sub=f"test-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        first_name="Test",
        last_name="User",
        profile_photo_url=photo,
    )
    db.add(user)
    db.commit()
    user_id = str(user.id)
    db.close()
    return user_id


def _me(user_id):
    return client.get("/api/auth/me", cookies=_cookie_for(user_id)).json()


def test_me_serves_our_own_stored_copy():
    user_id = _make_user("linkedin/abc.jpg")
    assert _me(user_id)["profile_photo_url"] == "/api/uploads/linkedin/abc.jpg"


def test_me_passes_through_a_legacy_full_url():
    """A row written before the store-our-own-copy fix holds LinkedIn's
    full URL - it must come back as-is, not mangled into
    /api/uploads/https://... (it gets replaced on that person's next
    login anyway)."""
    legacy = "https://media.licdn.com/dms/image/v2/x/profile.jpg?e=1791417600"
    user_id = _make_user(legacy)
    assert _me(user_id)["profile_photo_url"] == legacy


def test_me_with_no_photo():
    user_id = _make_user(None)
    assert _me(user_id)["profile_photo_url"] is None
