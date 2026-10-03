"""
Tests for compatibility scoring - see
app/services/compatibility_scoring.py. Covers the core ranking
guarantee (more overlap scores higher) and the individual weight
contributions, plus the full pipeline via the real API endpoint
(mirroring the 5-candidate scenario manually verified against
Postgres - see commit message for those exact results).
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
from app.models.activity import Activity, UserActivity
from app.models.interest import Interest, UserInterest
from app.models.user import User
from app.models.user_location import UserLocation
from app.models.user_social_profile import UserSocialProfile
from app.services.compatibility_scoring import get_ranked_candidates

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


def _make_location(db, user_id, lat=40.7128, lon=-74.0060, radius=25):
    loc = UserLocation(user_id=user_id, city="Test City", latitude=lat, longitude=lon, travel_radius_miles=radius, is_primary=True)
    db.add(loc)
    db.commit()
    return loc


def _make_activity(db, label):
    # Suffixed with a UUID - activities have a real unique-name
    # constraint (same one that caught the Pub Trivia/Trivia Nights
    # catalog duplicate), and this module's DB persists across every
    # test function in the file (module-scoped fixture), so two tests
    # both wanting e.g. "Shared Activity" would otherwise collide.
    a = Activity(id=uuid.uuid4(), name=f"{label} {uuid.uuid4()}", category="sports")
    db.add(a)
    db.commit()
    return a


def _make_interest(db, label):
    i = Interest(id=uuid.uuid4(), name=f"{label} {uuid.uuid4()}")
    db.add(i)
    db.commit()
    return i


def _select_activity(db, user_id, activity_id, loved, visible=True):
    db.add(UserActivity(user_id=user_id, activity_id=activity_id, is_top_pick=loved, visible_on_profile=visible))
    db.commit()


def _select_interest(db, user_id, interest_id, loved, visible=True):
    db.add(UserInterest(user_id=user_id, interest_id=interest_id, is_top_pick=loved, visible_on_profile=visible))
    db.commit()


def test_more_overlap_scores_higher():
    db = SessionLocal()
    a = _make_user(db)
    best = _make_user(db)
    none_shared = _make_user(db)
    _make_location(db, a.id)
    _make_location(db, best.id)
    _make_location(db, none_shared.id)

    activity = _make_activity(db, "Shared Activity")
    _select_activity(db, a.id, activity.id, loved=True)
    _select_activity(db, best.id, activity.id, loved=True)

    ranked = get_ranked_candidates(db, a.id)
    ranked_ids = [sc.user.id for sc in ranked]
    assert ranked_ids.index(best.id) < ranked_ids.index(none_shared.id)
    db.close()


def test_loved_activity_scores_higher_than_liked_only():
    db = SessionLocal()
    a = _make_user(db)
    loved_match = _make_user(db)
    liked_match = _make_user(db)
    _make_location(db, a.id)
    _make_location(db, loved_match.id)
    _make_location(db, liked_match.id)

    activity = _make_activity(db, "Test Activity")
    _select_activity(db, a.id, activity.id, loved=True)
    _select_activity(db, loved_match.id, activity.id, loved=True)
    _select_activity(db, liked_match.id, activity.id, loved=False)

    ranked = get_ranked_candidates(db, a.id)
    scores = {sc.user.id: sc.score for sc in ranked}
    assert scores[loved_match.id] > scores[liked_match.id], (
        "a shared LOVED activity should score higher than a shared LIKED-only activity - "
        "that's the entire point of weighting loved above liked"
    )
    db.close()


def test_shared_activity_outweighs_shared_interest():
    """Per the product's activities-first thesis, a shared loved
    activity should be worth more than a shared loved interest."""
    db = SessionLocal()
    a = _make_user(db)
    activity_match = _make_user(db)
    interest_match = _make_user(db)
    _make_location(db, a.id)
    _make_location(db, activity_match.id)
    _make_location(db, interest_match.id)

    activity = _make_activity(db, "Shared Activity")
    interest = _make_interest(db, "Shared Interest")
    _select_activity(db, a.id, activity.id, loved=True)
    _select_activity(db, activity_match.id, activity.id, loved=True)
    _select_interest(db, a.id, interest.id, loved=True)
    _select_interest(db, interest_match.id, interest.id, loved=True)

    ranked = get_ranked_candidates(db, a.id)
    scores = {sc.user.id: sc.score for sc in ranked}
    assert scores[activity_match.id] > scores[interest_match.id]
    db.close()


def test_closer_proximity_scores_higher_with_no_other_overlap():
    db = SessionLocal()
    a = _make_user(db)
    close = _make_user(db)
    far = _make_user(db)
    # Both candidates need a real travel_radius_miles generous enough to
    # stay ELIGIBLE (not just lower-scoring) at this distance - the
    # eligibility gate runs before scoring ever sees them. Distances
    # confirmed via the actual haversine helper, not guessed: ~0.6 miles
    # and ~26.5 miles respectively.
    _make_location(db, a.id, lat=40.7128, lon=-74.0060, radius=50)
    _make_location(db, close.id, lat=40.7200, lon=-74.0000, radius=50)  # ~0.6 miles away
    _make_location(db, far.id, lat=40.7128, lon=-73.5000, radius=50)  # ~26.5 miles away, still eligible

    ranked = get_ranked_candidates(db, a.id)
    scores = {sc.user.id: sc.score for sc in ranked}
    assert close.id in scores, "close candidate should be eligible"
    assert far.id in scores, "far candidate should still be eligible, just lower-scoring"
    assert scores[close.id] > scores[far.id]
    db.close()


def test_reasons_are_populated_for_a_real_match():
    db = SessionLocal()
    a = _make_user(db)
    match = _make_user(db)
    _make_location(db, a.id)
    _make_location(db, match.id)

    activity = _make_activity(db, "Hiking")
    _select_activity(db, a.id, activity.id, loved=True)
    _select_activity(db, match.id, activity.id, loved=True)

    ranked = get_ranked_candidates(db, a.id)
    match_result = next(sc for sc in ranked if sc.user.id == match.id)
    assert any("Hiking" in r for r in match_result.reasons)
    db.close()


def test_candidates_endpoint_returns_score_and_reasons():
    db = SessionLocal()
    a = _make_user(db)
    b = _make_user(db)
    _make_location(db, a.id)
    _make_location(db, b.id)
    a_id = str(a.id)
    db.close()

    cookies = _cookie_for(a_id)
    response = client.get("/api/discover/candidates", cookies=cookies)
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    assert "score" in body[0]
    assert "reasons" in body[0]


def test_reasons_do_not_name_items_the_candidate_hid_from_their_profile():
    """Privacy: a shared item the CANDIDATE marked not-visible-on-profile
    must still count toward the score (visibility controls public
    display, not matching eligibility) but must never be NAMED in the
    reasons text - naming it would reveal a selection they chose not to
    show anyone."""
    db = SessionLocal()
    a = _make_user(db)
    b = _make_user(db)
    _make_location(db, a.id)
    _make_location(db, b.id)

    shown = _make_activity(db, "ShownActivity")
    hidden = _make_activity(db, "HiddenActivity")
    hidden_interest = _make_interest(db, "HiddenInterest")
    for act in (shown, hidden):
        _select_activity(db, a.id, act.id, loved=True)
    _select_activity(db, b.id, shown.id, loved=True, visible=True)
    _select_activity(db, b.id, hidden.id, loved=True, visible=False)
    _select_interest(db, a.id, hidden_interest.id, loved=True)
    _select_interest(db, b.id, hidden_interest.id, loved=True, visible=False)

    ranked = get_ranked_candidates(db, a.id)
    result = next(sc for sc in ranked if sc.user.id == b.id)
    all_reasons = " | ".join(result.reasons)

    assert "ShownActivity" in all_reasons
    assert "HiddenActivity" not in all_reasons, "hidden activity name leaked into reasons"
    assert "HiddenInterest" not in all_reasons, "hidden interest name leaked into reasons"
    # ...but both loved activities still count toward the score and the count
    assert "2 shared loved activities" in all_reasons
    db.close()
