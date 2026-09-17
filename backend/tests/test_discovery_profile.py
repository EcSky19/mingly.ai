"""
Tests for location, interests, and activities endpoints - the "Stage 1"
pieces of the rest of Week 2 onboarding.
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
from app.models.interest import Interest
from app.models.activity import Activity

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Seed a small catalog for tests - mirrors migration 0004's seed data
    # but doesn't require running the full migration against SQLite.
    interests = [Interest(id=uuid.uuid4(), name=n) for n in ["Music", "Travel", "Fitness", "Cooking", "Books", "Art"]]
    activities = [
        Activity(id=uuid.uuid4(), name="Running", category="sports"),
        Activity(id=uuid.uuid4(), name="Dog Walks", category="pets"),
        Activity(id=uuid.uuid4(), name="Coffee", category="social_food"),
        Activity(id=uuid.uuid4(), name="Hiking", category="outdoor"),
    ]
    db.add_all(interests + activities)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clear_cookies_between_tests():
    """httpx's TestClient persists per-request cookies into its shared
    jar despite them being passed per-call (a known ambiguity - see the
    DeprecationWarning), which caused cookie bleed between tests here.
    Clearing before every test prevents one test's session from leaking
    into the next and silently authenticating a request that should be
    anonymous."""
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


# --- Interests ---

def test_interests_catalog_is_public():
    response = client.get("/api/catalog/interests")
    assert response.status_code == 200
    assert len(response.json()) == 6


def test_interests_requires_auth():
    assert client.get("/api/profile/interests").status_code == 401
    assert client.put("/api/profile/interests", json={"interest_ids": []}).status_code == 401


def test_set_and_get_interests_with_top_picks(test_user):
    cookies = _cookie_for(str(test_user.id))
    catalog = client.get("/api/catalog/interests").json()
    ids = [c["id"] for c in catalog[:4]]
    top = ids[:2]

    response = client.put(
        "/api/profile/interests",
        json={"interest_ids": ids, "top_pick_ids": top, "visible_on_profile": True},
        cookies=cookies,
    )
    assert response.status_code == 200

    fetched = client.get("/api/profile/interests", cookies=cookies).json()
    assert len(fetched) == 4
    assert sum(1 for f in fetched if f["is_top_pick"]) == 2


def test_top_picks_must_be_subset_of_selected(test_user):
    cookies = _cookie_for(str(test_user.id))
    catalog = client.get("/api/catalog/interests").json()
    ids = [catalog[0]["id"]]
    top = [catalog[1]["id"]]  # not in ids

    response = client.put(
        "/api/profile/interests",
        json={"interest_ids": ids, "top_pick_ids": top},
        cookies=cookies,
    )
    assert response.status_code == 400


def test_too_many_top_picks_rejected(test_user):
    cookies = _cookie_for(str(test_user.id))
    catalog = client.get("/api/catalog/interests").json()
    ids = [c["id"] for c in catalog]  # all 6

    response = client.put(
        "/api/profile/interests",
        json={"interest_ids": ids, "top_pick_ids": ids},  # 6 top picks, max is 5
        cookies=cookies,
    )
    assert response.status_code == 400


def test_invalid_interest_id_rejected(test_user):
    cookies = _cookie_for(str(test_user.id))
    response = client.put(
        "/api/profile/interests",
        json={"interest_ids": [str(uuid.uuid4())]},  # doesn't exist in catalog
        cookies=cookies,
    )
    assert response.status_code == 400


def test_setting_interests_replaces_previous_selection(test_user):
    """A second PUT should replace, not append to, the first."""
    cookies = _cookie_for(str(test_user.id))
    catalog = client.get("/api/catalog/interests").json()

    client.put("/api/profile/interests", json={"interest_ids": [catalog[0]["id"], catalog[1]["id"]]}, cookies=cookies)
    client.put("/api/profile/interests", json={"interest_ids": [catalog[2]["id"]]}, cookies=cookies)

    fetched = client.get("/api/profile/interests", cookies=cookies).json()
    assert len(fetched) == 1
    assert fetched[0]["name"] == catalog[2]["name"]


# --- Activities ---

def test_activities_requires_auth():
    assert client.get("/api/profile/activities").status_code == 401


def test_set_and_get_activities_with_context(test_user):
    cookies = _cookie_for(str(test_user.id))
    catalog = client.get("/api/catalog/activities").json()
    running = next(a for a in catalog if a["name"] == "Running")

    response = client.put(
        "/api/profile/activities",
        json={
            "activities": [
                {
                    "activity_id": running["id"],
                    "interest_strength": "high",
                    "skill_level": "intermediate",
                    "activity_style": "fitness_focused",
                    "desired_frequency": "weekly",
                    "preferred_group_size": "either",
                    "is_top_pick": True,
                    "target_timeframe": "sometime_soon",
                }
            ]
        },
        cookies=cookies,
    )
    assert response.status_code == 200

    fetched = client.get("/api/profile/activities", cookies=cookies).json()
    assert len(fetched) == 1
    assert fetched[0]["skill_level"] == "intermediate"
    assert fetched[0]["category"] == "sports"
    assert fetched[0]["is_top_pick"] is True
    assert fetched[0]["target_timeframe"] == "sometime_soon"


def test_activity_all_four_target_timeframes_accepted(test_user):
    """Confirms all four friendly timeframe options are valid, not just
    the one used in the main round-trip test above."""
    cookies = _cookie_for(str(test_user.id))
    catalog = client.get("/api/catalog/activities").json()

    for timeframe, activity in zip(
        ["ready_now", "sometime_soon", "when_season_right", "no_rush"], catalog
    ):
        response = client.put(
            "/api/profile/activities",
            json={"activities": [{"activity_id": activity["id"], "target_timeframe": timeframe}]},
            cookies=cookies,
        )
        assert response.status_code == 200, f"{timeframe} should be accepted"
        fetched = client.get("/api/profile/activities", cookies=cookies).json()
        assert fetched[0]["target_timeframe"] == timeframe


def test_activities_too_many_top_picks_rejected(test_user):
    cookies = _cookie_for(str(test_user.id))
    catalog = client.get("/api/catalog/activities").json()
    assert len(catalog) == 4, "test assumes 4 seeded activities so 4 top picks exceeds the max of 3"

    response = client.put(
        "/api/profile/activities",
        json={"activities": [{"activity_id": a["id"], "is_top_pick": True} for a in catalog]},
        cookies=cookies,
    )
    assert response.status_code == 400


# --- Locations ---

def test_locations_requires_auth():
    assert client.get("/api/profile/locations").status_code == 401


def test_multi_location_with_exactly_one_primary(test_user):
    cookies = _cookie_for(str(test_user.id))

    r1 = client.post("/api/profile/locations", json={"city": "New York", "is_primary": True}, cookies=cookies)
    assert r1.status_code == 201
    loc1_id = r1.json()["id"]

    r2 = client.post("/api/profile/locations", json={"city": "Boston", "is_primary": True}, cookies=cookies)
    assert r2.status_code == 201

    locations = client.get("/api/profile/locations", cookies=cookies).json()
    assert len(locations) == 2
    primaries = [l for l in locations if l["is_primary"]]
    assert len(primaries) == 1, "exactly one location should be primary, even after two POSTs both claiming primary"
    assert primaries[0]["city"] == "Boston"

    client.delete(f"/api/profile/locations/{loc1_id}", cookies=cookies)
    remaining = client.get("/api/profile/locations", cookies=cookies).json()
    assert len(remaining) == 1
    assert remaining[0]["city"] == "Boston"


def test_location_delete_scoped_to_owner(test_user):
    cookies = _cookie_for(str(test_user.id))

    other_db = SessionLocal()
    other_user = User(
        linkedin_sub=f"test-other-{uuid.uuid4()}",
        email=f"test-other-{uuid.uuid4()}@example.com",
        first_name="Other",
        last_name="User",
    )
    other_db.add(other_user)
    other_db.commit()
    other_db.refresh(other_user)
    other_cookies = _cookie_for(str(other_user.id))

    create_resp = client.post("/api/profile/locations", json={"city": "Chicago"}, cookies=other_cookies)
    other_location_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/profile/locations/{other_location_id}", cookies=cookies)
    assert delete_resp.status_code == 404

    still_there = client.get("/api/profile/locations", cookies=other_cookies).json()
    assert any(l["id"] == other_location_id for l in still_there)

    other_db.close()
