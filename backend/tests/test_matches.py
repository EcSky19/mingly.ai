"""
Tests for mutual matches and the optional match contact info. The core
privacy guarantee: someone's contact is only ever visible to their
CURRENT mutual matches - never on a one-sided interest, never to a third
person, never in Discovery, and never again after an unmatch.
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


def _person(name="Test", status="active"):
    db = SessionLocal()
    user = User(
        linkedin_sub=f"t-{uuid.uuid4()}", email=f"t-{uuid.uuid4()}@example.com",
        first_name=name, last_name="U", account_status=status, onboarding_completed=True,
    )
    db.add(user)
    db.commit()
    db.add(UserLocation(user_id=user.id, city="NYC", latitude=40.7128, longitude=-74.0060, travel_radius_miles=25, is_primary=True))
    db.commit()
    user_id = str(user.id)
    db.close()
    return user_id, _cookie_for(user_id)


def _interested(cookies, target_id):
    return client.post("/api/discover/interact", json={"target_user_id": target_id, "action": "interested"}, cookies=cookies).json()


# --- Match contact (your own) ---

def test_match_contact_requires_auth():
    assert client.get("/api/profile/match-contact").status_code == 401
    assert client.put("/api/profile/match-contact", json={}).status_code == 401


def test_match_contact_is_normalized_and_partially_updatable():
    _, cookies = _person()
    saved = client.put(
        "/api/profile/match-contact",
        json={"linkedin_url": "linkedin.com/in/Me-Here/?utm_source=share", "phone": "+1 (917) 555-0123", "instagram": "@my.handle"},
        cookies=cookies,
    ).json()
    assert saved == {"linkedin_url": "https://www.linkedin.com/in/me-here", "phone": "+1 (917) 555-0123", "instagram": "my.handle"}

    after = client.put("/api/profile/match-contact", json={"phone": ""}, cookies=cookies).json()
    assert after["phone"] is None and after["linkedin_url"] == "https://www.linkedin.com/in/me-here", "blank clears; omitted fields untouched"


@pytest.mark.parametrize("bad", [{"linkedin_url": "https://evil.com/in/x"}, {"linkedin_url": "https://linkedin.com.evil.com/in/x"}, {"linkedin_url": "linkedin.com/company/acme"}, {"phone": "12"}, {"instagram": "has spaces!"}])
def test_invalid_match_contact_rejected(bad):
    _, cookies = _person()
    assert client.put("/api/profile/match-contact", json=bad, cookies=cookies).status_code == 422


# --- Mutual matches ---

def test_one_sided_interest_is_not_a_match_and_reveals_nothing():
    a, a_cookies = _person("Avery")
    b, b_cookies = _person("Blake")
    client.put("/api/profile/match-contact", json={"linkedin_url": "linkedin.com/in/avery-secret"}, cookies=a_cookies)

    assert _interested(a_cookies, b)["matched"] is False
    assert client.get("/api/matches", cookies=a_cookies).json() == []
    assert client.get("/api/matches", cookies=b_cookies).json() == []
    assert "avery-secret" not in json.dumps(client.get("/api/discover/candidates", cookies=b_cookies).json())


def test_mutual_interest_is_a_match_and_shares_contact_both_ways():
    a, a_cookies = _person("Avery")
    b, b_cookies = _person("Blake")
    client.put("/api/profile/match-contact", json={"linkedin_url": "linkedin.com/in/avery-secret"}, cookies=a_cookies)

    _interested(a_cookies, b)
    assert _interested(b_cookies, a)["matched"] is True, "second 'interested' completes the match"

    blakes = client.get("/api/matches", cookies=b_cookies).json()
    assert [m["id"] for m in blakes] == [a]
    assert blakes[0]["contact"]["linkedin_url"] == "https://www.linkedin.com/in/avery-secret"
    averys = client.get("/api/matches", cookies=a_cookies).json()
    assert [m["id"] for m in averys] == [b]
    assert averys[0]["contact"] == {"linkedin_url": None, "phone": None, "instagram": None}


def test_contact_never_visible_to_a_third_person():
    a, a_cookies = _person("Avery")
    b, b_cookies = _person("Blake")
    _, c_cookies = _person("Casey")
    client.put("/api/profile/match-contact", json={"linkedin_url": "linkedin.com/in/avery-secret", "instagram": "avery.ig"}, cookies=a_cookies)
    _interested(a_cookies, b)
    _interested(b_cookies, a)

    for path in ("/api/matches", "/api/discover/candidates"):
        raw = json.dumps(client.get(path, cookies=c_cookies).json())
        assert "avery-secret" not in raw and "avery.ig" not in raw


def test_unmatch_ends_it_for_both_and_hides_contact_immediately():
    a, a_cookies = _person("Avery")
    b, b_cookies = _person("Blake")
    client.put("/api/profile/match-contact", json={"linkedin_url": "linkedin.com/in/avery-secret"}, cookies=a_cookies)
    _interested(a_cookies, b)
    _interested(b_cookies, a)

    assert client.delete(f"/api/matches/{b}", cookies=a_cookies).status_code == 204
    assert client.get("/api/matches", cookies=a_cookies).json() == []
    assert client.get("/api/matches", cookies=b_cookies).json() == []
    raw = json.dumps([client.get(p, cookies=b_cookies).json() for p in ("/api/matches", "/api/discover/candidates")])
    assert "avery-secret" not in raw


def test_unmatching_someone_you_are_not_matched_with_404s():
    _, a_cookies = _person("Avery")
    b, _ = _person("Blake")
    assert client.delete(f"/api/matches/{b}", cookies=a_cookies).status_code == 404
    assert client.delete("/api/matches/not-a-uuid", cookies=a_cookies).status_code == 404


def test_suspended_account_disappears_from_matches():
    a, a_cookies = _person("Avery")
    b, b_cookies = _person("Blake")
    _interested(a_cookies, b)
    _interested(b_cookies, a)

    db = SessionLocal()
    db.query(User).filter(User.id == uuid.UUID(b)).update({"account_status": "suspended"})
    db.commit()
    db.close()
    assert client.get("/api/matches", cookies=a_cookies).json() == []


def test_matches_require_auth():
    assert client.get("/api/matches").status_code == 401
    assert client.delete(f"/api/matches/{uuid.uuid4()}").status_code == 401


def _feed_ids(cookies):
    return [c["id"] for c in client.get("/api/discover/candidates", cookies=cookies).json()]


def test_someone_interested_in_you_stays_in_your_feed_so_you_can_match_back():
    """The real path, through the feed: Avery taps Interested on Blake.
    Blake must still see Avery in Discovery, or he could never match back."""
    a, a_cookies = _person("Avery")
    b, b_cookies = _person("Blake")
    assert b in _feed_ids(a_cookies)
    _interested(a_cookies, b)
    assert a in _feed_ids(b_cookies), "Avery vanished from Blake's feed - he can never match back"
    s = client.post("/api/discover/interact", json={"target_user_id": a, "action": "interested"}, cookies=b_cookies).json()
    assert s["matched"] is True


def test_people_you_decided_on_leave_your_feed_and_people_who_passed_on_you_too():
    a, a_cookies = _person("Avery")
    b, b_cookies = _person("Blake")
    c, c_cookies = _person("Casey")
    _interested(a_cookies, b)
    client.post("/api/discover/interact", json={"target_user_id": c, "action": "dismissed"}, cookies=a_cookies)
    feed = _feed_ids(a_cookies)
    assert b not in feed and c not in feed, "people you've decided on leave your own feed"
    assert a not in _feed_ids(c_cookies), "someone who passed on you shouldn't keep appearing in your feed"


# --- Decide later ---

def _act(cookies, target_id, action):
    return client.post("/api/discover/interact", json={"target_user_id": target_id, "action": action}, cookies=cookies).json()


def test_decide_later_keeps_them_in_your_feed_behind_everyone_else():
    a, a_cookies = _person("Avery")
    b, _ = _person("Blake")
    c, _ = _person("Casey")
    assert _act(a_cookies, b, "later")["matched"] is False
    feed = client.get("/api/discover/candidates", cookies=a_cookies).json()
    ids = [x["id"] for x in feed]
    assert b in ids and c in ids, "deferring doesn't remove anyone"
    assert ids.index(c) < ids.index(b), "deferred people come after people you haven't decided on"
    assert next(x for x in feed if x["id"] == b)["deferred"] is True
    assert next(x for x in feed if x["id"] == c)["deferred"] is False


def test_decide_later_is_private_and_never_counts_as_interest():
    a, a_cookies = _person("Avery")
    b, b_cookies = _person("Blake")
    _act(a_cookies, b, "later")
    assert a in [x["id"] for x in client.get("/api/discover/candidates", cookies=b_cookies).json()], "they still see you"
    assert _act(b_cookies, a, "interested")["matched"] is False, "'later' is not interest"
    assert client.get("/api/matches", cookies=b_cookies).json() == []


def test_you_can_still_match_after_deciding_later():
    a, a_cookies = _person("Avery")
    b, b_cookies = _person("Blake")
    _act(a_cookies, b, "later")
    _act(b_cookies, a, "interested")
    assert _act(a_cookies, b, "interested")["matched"] is True
    assert b not in [x["id"] for x in client.get("/api/discover/candidates", cookies=a_cookies).json()]
