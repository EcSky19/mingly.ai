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
        "spending_preference": "moderate",
        "city_circle_status": "know_some_want_to_expand",
        "comfortable_with_dogs": True,
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
    assert fetched["spending_preference"] == "moderate"
    assert fetched["city_circle_status"] == "know_some_want_to_expand"
    assert fetched["comfortable_with_dogs"] is True
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


def test_gender_identity_full_round_trip(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put(
        "/api/profile/social",
        json={
            "gender_identity": "non_binary",
            "gender_identity_visible_on_profile": True,
            "gender_identity_usable_for_matching": True,
        },
        cookies=cookies,
    )
    assert response.status_code == 200
    fetched = client.get("/api/profile/social", cookies=cookies).json()
    assert fetched["gender_identity"] == "non_binary"
    assert fetched["gender_identity_visible_on_profile"] is True


def test_gender_identity_self_describe_text(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put(
        "/api/profile/social",
        json={"gender_identity": "self_describe", "gender_identity_description": "Genderfluid"},
        cookies=cookies,
    )
    assert response.status_code == 200
    fetched = client.get("/api/profile/social", cookies=cookies).json()
    assert fetched["gender_identity_description"] == "Genderfluid"


def test_mingle_preference_multiple_groups(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put(
        "/api/profile/social", json={"mingle_preference": ["women", "non_binary"]}, cookies=cookies
    )
    assert response.status_code == 200
    fetched = client.get("/api/profile/social", cookies=cookies).json()
    assert fetched["mingle_preference"] == ["women", "non_binary"]


def test_mingle_preference_everyone_alone_allowed(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put("/api/profile/social", json={"mingle_preference": ["everyone"]}, cookies=cookies)
    assert response.status_code == 200


def test_mingle_preference_everyone_combined_with_specific_rejected(test_user):
    """The core validation rule: 'everyone' is mutually exclusive with
    specific groups - selecting both doesn't make sense and should be
    rejected server-side, not just prevented in the UI."""
    cookies = _cookie_for(str(test_user.id))
    response = client.put(
        "/api/profile/social", json={"mingle_preference": ["everyone", "women"]}, cookies=cookies
    )
    assert response.status_code == 422


def test_mingle_preference_invalid_value_rejected(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put("/api/profile/social", json={"mingle_preference": ["aliens"]}, cookies=cookies)
    assert response.status_code == 422


def test_mingle_preference_has_no_privacy_fields(test_user):
    """Structural check: confirms there is genuinely no field to expose
    mingle_preference's visibility - private by design, not just
    unused. If someone ever added such a field by mistake, this test
    would need explicit updating to still pass, which is the point."""
    cookies = _cookie_for(str(test_user.id))
    client.put("/api/profile/social", json={"mingle_preference": ["everyone"]}, cookies=cookies)
    fetched = client.get("/api/profile/social", cookies=cookies).json()
    assert "mingle_preference_visible_on_profile" not in fetched
    assert "mingle_preference_usable_for_matching" not in fetched


def test_age_range_full_round_trip(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put(
        "/api/profile/social",
        json={
            "age_range": "25_29",
            "age_range_visible_on_profile": True,
            "age_range_usable_for_matching": True,
        },
        cookies=cookies,
    )
    assert response.status_code == 200
    fetched = client.get("/api/profile/social", cookies=cookies).json()
    assert fetched["age_range"] == "25_29"
    assert fetched["age_range_visible_on_profile"] is True


def test_age_range_prefer_not_to_say(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put("/api/profile/social", json={"age_range": "prefer_not_to_say"}, cookies=cookies)
    assert response.status_code == 200
    fetched = client.get("/api/profile/social", cookies=cookies).json()
    assert fetched["age_range"] == "prefer_not_to_say"


def test_age_preference_multiple_buckets(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put(
        "/api/profile/social", json={"age_preference": ["25_29", "30_34"]}, cookies=cookies
    )
    assert response.status_code == 200
    fetched = client.get("/api/profile/social", cookies=cookies).json()
    assert fetched["age_preference"] == ["25_29", "30_34"]


def test_age_preference_everyone_alone_allowed(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put("/api/profile/social", json={"age_preference": ["everyone"]}, cookies=cookies)
    assert response.status_code == 200


def test_age_preference_everyone_combined_with_specific_rejected(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put(
        "/api/profile/social", json={"age_preference": ["everyone", "25_29"]}, cookies=cookies
    )
    assert response.status_code == 422


def test_age_preference_invalid_value_rejected(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put("/api/profile/social", json={"age_preference": ["100_plus"]}, cookies=cookies)
    assert response.status_code == 422


def test_age_preference_has_no_privacy_fields(test_user):
    """Same structural guard as mingle_preference above."""
    cookies = _cookie_for(str(test_user.id))
    client.put("/api/profile/social", json={"age_preference": ["everyone"]}, cookies=cookies)
    fetched = client.get("/api/profile/social", cookies=cookies).json()
    assert "age_preference_visible_on_profile" not in fetched
    assert "age_preference_usable_for_matching" not in fetched


def test_saving_lifestyle_fields_does_not_wipe_about_you_settings(test_user):
    """The onboarding page saves ONLY lifestyle fields. That must never
    reset About You settings (set separately on /profile) - wiping a
    narrowed mingle preference would silently widen it to 'everyone'."""
    cookies = _cookie_for(str(test_user.id))
    client.put(
        "/api/profile/social",
        json={"gender_identity": "woman", "mingle_preference": ["women"], "age_range": "25_29", "age_preference": ["25_29"]},
        cookies=cookies,
    )
    # Exactly the shape the onboarding page sends: lifestyle fields only
    client.put(
        "/api/profile/social",
        json={"activity_level": "active", "visible_on_profile": True, "usable_for_matching": True},
        cookies=cookies,
    )
    fetched = client.get("/api/profile/social", cookies=cookies).json()
    assert fetched["activity_level"] == "active"
    assert fetched["gender_identity"] == "woman"
    assert fetched["mingle_preference"] == ["women"], "narrowed mingle preference was silently wiped"
    assert fetched["age_range"] == "25_29"
    assert fetched["age_preference"] == ["25_29"]


def test_explicit_null_still_clears_a_field(test_user):
    """Partial updates must still allow deliberately clearing a field -
    sending null clears it; omitting it leaves it alone."""
    cookies = _cookie_for(str(test_user.id))
    client.put("/api/profile/social", json={"drinking_preference": "social"}, cookies=cookies)
    client.put("/api/profile/social", json={"drinking_preference": None}, cookies=cookies)
    assert client.get("/api/profile/social", cookies=cookies).json()["drinking_preference"] is None
