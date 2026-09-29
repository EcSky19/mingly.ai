"""
Tests for hard eligibility filtering - see app/services/eligibility.py.
Covers each filter dimension independently, plus the full pipeline via
the API endpoint (mirroring the real end-to-end scenario manually
verified against Postgres).
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
from app.models.user_interaction import UserInteraction
from app.models.user_location import UserLocation
from app.models.user_social_profile import UserSocialProfile
from app.services.eligibility import get_eligible_candidates

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


def _make_user(db, **overrides):
    defaults = dict(
        linkedin_sub=f"test-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        first_name="Test",
        last_name="User",
        account_status="active",
        onboarding_completed=True,
    )
    defaults.update(overrides)
    user = User(**defaults)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_social(db, user_id, **overrides):
    defaults = dict(user_id=user_id, visible_on_profile=False, usable_for_matching=True)
    defaults.update(overrides)
    profile = UserSocialProfile(**defaults)
    db.add(profile)
    db.commit()
    return profile


def _make_location(db, user_id, lat, lon, radius=20):
    loc = UserLocation(user_id=user_id, city="Test City", latitude=lat, longitude=lon, travel_radius_miles=radius, is_primary=True)
    db.add(loc)
    db.commit()
    return loc


NYC = (40.7128, -74.0060)
NYC_NEARBY = (40.7300, -73.9950)  # ~2 miles from NYC
LA = (34.0522, -118.2437)  # ~2500 miles from NYC


def test_basic_eligible_candidate_included():
    db = SessionLocal()
    a = _make_user(db)
    b = _make_user(db)
    _make_location(db, a.id, *NYC)
    _make_location(db, b.id, *NYC_NEARBY)
    result = get_eligible_candidates(db, a.id)
    assert b.id in [c.id for c in result]
    db.close()


def test_inactive_account_excluded():
    db = SessionLocal()
    a = _make_user(db)
    b = _make_user(db, account_status="suspended")
    _make_location(db, a.id, *NYC)
    _make_location(db, b.id, *NYC_NEARBY)
    result = get_eligible_candidates(db, a.id)
    assert b.id not in [c.id for c in result]
    db.close()


def test_incomplete_onboarding_excluded():
    db = SessionLocal()
    a = _make_user(db)
    b = _make_user(db, onboarding_completed=False)
    _make_location(db, a.id, *NYC)
    _make_location(db, b.id, *NYC_NEARBY)
    result = get_eligible_candidates(db, a.id)
    assert b.id not in [c.id for c in result]
    db.close()


def test_self_excluded():
    db = SessionLocal()
    a = _make_user(db)
    _make_location(db, a.id, *NYC)
    result = get_eligible_candidates(db, a.id)
    assert a.id not in [c.id for c in result]
    db.close()


def test_already_interacted_excluded_either_direction():
    db = SessionLocal()
    a = _make_user(db)
    b = _make_user(db)
    c = _make_user(db)
    _make_location(db, a.id, *NYC)
    _make_location(db, b.id, *NYC_NEARBY)
    _make_location(db, c.id, *NYC_NEARBY)
    # A dismissed B
    db.add(UserInteraction(user_id=a.id, target_user_id=b.id, action="dismissed"))
    # C dismissed A (reverse direction)
    db.add(UserInteraction(user_id=c.id, target_user_id=a.id, action="dismissed"))
    db.commit()
    result_ids = [c.id for c in get_eligible_candidates(db, a.id)]
    assert b.id not in result_ids
    assert c.id not in result_ids
    db.close()


def test_gender_mismatch_excluded():
    db = SessionLocal()
    a = _make_user(db)
    b = _make_user(db)
    _make_social(db, a.id, gender_identity="man", mingle_preference=["women"])
    _make_social(db, b.id, gender_identity="man", mingle_preference=["everyone"])
    _make_location(db, a.id, *NYC)
    _make_location(db, b.id, *NYC_NEARBY)
    result = get_eligible_candidates(db, a.id)
    assert b.id not in [c.id for c in result]
    db.close()


def test_gender_bidirectional_check():
    """A would accept B, but B's own preference doesn't want A's gender -
    B should still be excluded, since it's not a match either way."""
    db = SessionLocal()
    a = _make_user(db)
    b = _make_user(db)
    _make_social(db, a.id, gender_identity="man", mingle_preference=["everyone"])
    _make_social(db, b.id, gender_identity="woman", mingle_preference=["women"])
    _make_location(db, a.id, *NYC)
    _make_location(db, b.id, *NYC_NEARBY)
    result = get_eligible_candidates(db, a.id)
    assert b.id not in [c.id for c in result]
    db.close()


def test_self_describe_gender_only_reachable_via_everyone():
    db = SessionLocal()
    a = _make_user(db)
    b = _make_user(db)
    c = _make_user(db)
    _make_social(db, a.id, mingle_preference=["women"])  # narrowed, not "everyone"
    _make_social(db, b.id, gender_identity="self_describe", mingle_preference=["everyone"])
    _make_location(db, a.id, *NYC)
    _make_location(db, b.id, *NYC_NEARBY)
    result = get_eligible_candidates(db, a.id)
    assert b.id not in [c.id for c in result], "narrowed preference shouldn't reach self_describe"

    _make_social(db, c.id, mingle_preference=["everyone"])
    d = _make_user(db)
    _make_social(db, d.id, gender_identity="self_describe", mingle_preference=["everyone"])
    _make_location(db, c.id, *NYC)
    _make_location(db, d.id, *NYC_NEARBY)
    result2 = get_eligible_candidates(db, c.id)
    assert d.id in [x.id for x in result2], "everyone preference should reach self_describe"
    db.close()


def test_age_mismatch_excluded():
    db = SessionLocal()
    a = _make_user(db)
    b = _make_user(db)
    _make_social(db, a.id, age_preference=["18_24"])
    _make_social(db, b.id, age_range="40_49")
    _make_location(db, a.id, *NYC)
    _make_location(db, b.id, *NYC_NEARBY)
    result = get_eligible_candidates(db, a.id)
    assert b.id not in [c.id for c in result]
    db.close()


def test_too_far_away_excluded():
    db = SessionLocal()
    a = _make_user(db)
    b = _make_user(db)
    _make_location(db, a.id, *NYC, radius=20)
    _make_location(db, b.id, *LA, radius=20)
    result = get_eligible_candidates(db, a.id)
    assert b.id not in [c.id for c in result]
    db.close()


def test_respects_smaller_of_both_radii():
    """Even if A's radius would cover B, if B's own stated radius is
    smaller than the distance between them, B should still be excluded -
    the check respects BOTH people's stated willingness, not just A's."""
    db = SessionLocal()
    a = _make_user(db)
    b = _make_user(db)
    # ~2 miles apart
    _make_location(db, a.id, *NYC, radius=25)
    _make_location(db, b.id, *NYC_NEARBY, radius=1)  # B only wants 1 mile
    result = get_eligible_candidates(db, a.id)
    assert b.id not in [c.id for c in result]
    db.close()


def test_candidates_endpoint_requires_auth():
    assert client.get("/api/discover/candidates").status_code == 401


def test_candidates_endpoint_full_pipeline():
    db = SessionLocal()
    a = _make_user(db)
    b = _make_user(db)  # eligible
    c = _make_user(db, onboarding_completed=False)  # excluded
    _make_location(db, a.id, *NYC)
    _make_location(db, b.id, *NYC_NEARBY)
    _make_location(db, c.id, *NYC_NEARBY)
    a_id, b_id, c_id = str(a.id), str(b.id), str(c.id)
    db.close()

    cookies = _cookie_for(a_id)
    response = client.get("/api/discover/candidates", cookies=cookies)
    assert response.status_code == 200
    ids = [row["id"] for row in response.json()]
    assert b_id in ids
    assert c_id not in ids


def test_candidate_lookup_is_not_n_plus_one():
    """Proves the query count stays flat regardless of candidate count -
    not just an assumption. Counts real executed SQL statements via
    SQLAlchemy's event system with 2 candidates vs 8 candidates; if the
    old per-candidate query pattern were still there, the query count
    would scale with the candidate count. With the batch-fetch fix, it
    shouldn't."""
    from sqlalchemy import event

    def _make_scenario(db, n_candidates):
        a = _make_user(db)
        _make_location(db, a.id, *NYC)
        for _ in range(n_candidates):
            b = _make_user(db)
            _make_location(db, b.id, *NYC_NEARBY)
        return a.id

    def _count_queries(user_id):
        count = 0

        def _on_execute(*args, **kwargs):
            nonlocal count
            count += 1

        db = SessionLocal()
        event.listen(db.bind, "before_cursor_execute", _on_execute)
        try:
            get_eligible_candidates(db, user_id)
        finally:
            event.remove(db.bind, "before_cursor_execute", _on_execute)
            db.close()
        return count

    db1 = SessionLocal()
    small_user_id = _make_scenario(db1, 2)
    db1.close()
    small_count = _count_queries(small_user_id)

    db2 = SessionLocal()
    large_user_id = _make_scenario(db2, 8)
    db2.close()
    large_count = _count_queries(large_user_id)

    assert small_count == large_count, (
        f"Query count should be flat regardless of candidate count "
        f"(2 candidates: {small_count} queries, 8 candidates: {large_count} queries) - "
        f"if this fails, the N+1 pattern has regressed."
    )
