"""
Tests for the social profile endpoint (lifestyle, career orientation,
social preferences - the "Stage A" batch).
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


@pytest.fixture
def test_user():
    db = SessionLocal()
    user = User(
        linkedin_sub=f"test-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        first_name="Test",
        last_name="User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.close()


def _cookie_for(user_id: str) -> dict:
    signer = itsdangerous.TimestampSigner(settings.SESSION_SECRET)
    data = b64encode(json.dumps({"user_id": user_id}).encode("utf-8"))
    return {settings.SESSION_COOKIE_NAME: signer.sign(data).decode("utf-8")}


def test_social_profile_requires_auth():
    assert client.get("/api/profile/social").status_code == 401
    assert client.put("/api/profile/social", json={}).status_code == 401


def test_social_profile_starts_empty(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.get("/api/profile/social", cookies=cookies)
    assert response.status_code == 200
    body = response.json()
    assert body["career_orientation"] is None
    assert body["social_goals"] is None


def test_social_profile_full_round_trip(test_user):
    cookies = _cookie_for(str(test_user.id))
    payload = {
        "career_orientation": "very_career_driven",
        "career_qualities": ["ambitious", "curious"],
        "early_bird_night_owl": "night_owl",
        "activity_level": "active",
        "drinking_preference": "social_drinker",
        "going_out_frequency": "often",
        "indoor_outdoor_preference": "either",
        "weekday_weekend_preference": "weekends",
        "social_cadence": "about_once_per_week",
        "planning_style": "flexible",
        "meeting_preference": "small_groups",
        "social_environment": ["activity_focused", "outdoors"],
        "social_goals": ["activity_partners", "broader_social_circle"],
        "visible_on_profile": True,
        "usable_for_matching": True,
    }
    response = client.put("/api/profile/social", json=payload, cookies=cookies)
    assert response.status_code == 200

    fetched = client.get("/api/profile/social", cookies=cookies).json()
    assert fetched["career_orientation"] == "very_career_driven"
    assert fetched["career_qualities"] == ["ambitious", "curious"]
    assert fetched["social_environment"] == ["activity_focused", "outdoors"]
    assert fetched["social_goals"] == ["activity_partners", "broader_social_circle"]
    assert fetched["visible_on_profile"] is True


def test_social_profile_partial_update_preserved_on_refetch(test_user):
    """A user who only fills in lifestyle fields (not career orientation
    yet) should see exactly that partial state reflected back, not have
    unset fields silently defaulted to something misleading."""
    cookies = _cookie_for(str(test_user.id))
    response = client.put(
        "/api/profile/social",
        json={"activity_level": "relaxed", "drinking_preference": "non_drinker"},
        cookies=cookies,
    )
    assert response.status_code == 200
    fetched = client.get("/api/profile/social", cookies=cookies).json()
    assert fetched["activity_level"] == "relaxed"
    assert fetched["drinking_preference"] == "non_drinker"
    assert fetched["career_orientation"] is None


def test_invalid_career_quality_rejected(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put(
        "/api/profile/social", json={"career_qualities": ["not_a_real_quality"]}, cookies=cookies
    )
    assert response.status_code == 422


def test_invalid_social_goal_rejected(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put(
        "/api/profile/social", json={"social_goals": ["dating"]}, cookies=cookies
    )
    assert response.status_code == 422


def test_invalid_social_environment_rejected(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put(
        "/api/profile/social", json={"social_environment": ["not_real"]}, cookies=cookies
    )
    assert response.status_code == 422


def test_invalid_enum_value_rejected(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put(
        "/api/profile/social", json={"career_orientation": "not_a_real_value"}, cookies=cookies
    )
    assert response.status_code == 422
