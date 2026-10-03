"""
Tests for POST /api/auth/onboarding-complete.

The eligibility tests elsewhere create users with onboarding_completed
already true - a shortcut that let a real bug hide: nothing in the app
ever set that flag, so no real user was ever matchable. The regression
test here deliberately follows the REAL path instead: users start with
the model's defaults, exactly as a LinkedIn signup creates them.
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
from app.models.user_location import UserLocation

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


def _signup_like_user(lat=40.7128, lon=-74.0060) -> str:
    """Created the way the LinkedIn callback creates users - no explicit
    onboarding_completed, so it gets the model default (false) - plus a
    location, as onboarding would save."""
    db = SessionLocal()
    user = User(
        linkedin_sub=f"test-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        first_name="Test",
        last_name="User",
    )
    db.add(user)
    db.commit()
    db.add(UserLocation(user_id=user.id, city="NYC", latitude=lat, longitude=lon, travel_radius_miles=25, is_primary=True))
    db.commit()
    user_id = str(user.id)
    db.close()
    return user_id


def test_requires_auth():
    assert client.post("/api/auth/onboarding-complete").status_code == 401


def test_new_users_start_not_onboarded():
    user_id = _signup_like_user()
    assert client.get("/api/auth/me", cookies=_cookie_for(user_id)).json()["onboarding_completed"] is False


def test_marks_onboarding_complete_and_is_idempotent():
    user_id = _signup_like_user()
    cookies = _cookie_for(user_id)
    assert client.post("/api/auth/onboarding-complete", cookies=cookies).status_code == 200
    assert client.post("/api/auth/onboarding-complete", cookies=cookies).status_code == 200
    assert client.get("/api/auth/me", cookies=cookies).json()["onboarding_completed"] is True


def test_real_path_two_signups_become_matchable_only_after_completing_onboarding():
    """The regression test for the real bug: two people sign up and save
    nearby locations. Until they complete onboarding they can't see each
    other; once both do, they can."""
    a = _signup_like_user(lat=40.7128, lon=-74.0060)
    b = _signup_like_user(lat=40.7200, lon=-74.0000)
    cookies_a, cookies_b = _cookie_for(a), _cookie_for(b)

    before = [c["id"] for c in client.get("/api/discover/candidates", cookies=cookies_a).json()]
    assert b not in before, "should not be matchable before completing onboarding"

    client.post("/api/auth/onboarding-complete", cookies=cookies_a)
    client.post("/api/auth/onboarding-complete", cookies=cookies_b)

    after = [c["id"] for c in client.get("/api/discover/candidates", cookies=cookies_a).json()]
    assert b in after, "both completed onboarding nearby - they should now see each other"
