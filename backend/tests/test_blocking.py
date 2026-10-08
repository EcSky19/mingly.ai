"""
Blocking separates two people everywhere, in both directions: Discover,
matches and contact info, circles and circle requests, friend-of-friend
introductions, and the Connect action. Reporting reaches the team and, by
default, blocks too.
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
from app.models.circle import CircleRequest
from app.models.safety import UserReport
from app.models.user import User
from app.models.user_location import UserLocation
from app.services.circles import connect, request_from_invite

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


def _person(name="Test"):
    db = SessionLocal()
    u = User(linkedin_sub=f"t-{uuid.uuid4()}", email=f"t-{uuid.uuid4()}@example.com", first_name=name, last_name="U",
             account_status="active", onboarding_completed=True)
    db.add(u)
    db.commit()
    db.add(UserLocation(user_id=u.id, city="NYC", latitude=40.7128, longitude=-74.0060, travel_radius_miles=25, is_primary=True))
    db.commit()
    uid = str(u.id)
    db.close()
    signer = itsdangerous.TimestampSigner(settings.SESSION_SECRET)
    cookie = signer.sign(b64encode(json.dumps({"user_id": uid}).encode())).decode()
    return uid, {settings.SESSION_COOKIE_NAME: cookie}


def _feed(cookies):
    return [c["id"] for c in client.get("/api/discover/candidates", cookies=cookies).json()]


def _connect(cookies, target):
    return client.post("/api/discover/interact", json={"target_user_id": target, "action": "interested"}, cookies=cookies)


def _block(cookies, target):
    return client.post("/api/blocks", json={"user_id": target}, cookies=cookies)


def test_blocking_removes_both_people_from_each_others_discover():
    a, a_c = _person("Avery")
    b, b_c = _person("Blake")
    assert b in _feed(a_c) and a in _feed(b_c)
    assert _block(a_c, b).status_code == 204
    assert b not in _feed(a_c)
    assert a not in _feed(b_c), "the blocked person must not see the blocker either"


def test_blocking_ends_a_match_and_hides_contact_both_ways():
    a, a_c = _person("Avery")
    b, b_c = _person("Blake")
    client.put("/api/profile/match-contact", json={"instagram": "avery.secret"}, cookies=a_c)
    _connect(a_c, b)
    assert _connect(b_c, a).json()["matched"] is True
    _block(b_c, a)
    for cookies in (a_c, b_c):
        assert client.get("/api/matches", cookies=cookies).json() == []
    assert "avery.secret" not in json.dumps(client.get("/api/matches", cookies=b_c).json())


def test_unblocking_never_resurrects_a_match():
    a, a_c = _person("Avery")
    b, b_c = _person("Blake")
    _connect(a_c, b)
    _connect(b_c, a)
    _block(a_c, b)
    assert client.delete(f"/api/blocks/{b}", cookies=a_c).status_code == 204
    assert client.get("/api/matches", cookies=a_c).json() == []
    assert client.get("/api/matches", cookies=b_c).json() == []


def test_connecting_with_someone_who_blocked_you_looks_like_they_dont_exist():
    a, a_c = _person("Avery")
    b, b_c = _person("Blake")
    _block(a_c, b)
    blocked = _connect(b_c, a)
    missing = _connect(b_c, str(uuid.uuid4()))
    assert blocked.status_code == missing.status_code == 400
    assert blocked.json() == missing.json(), "the response must not reveal the block"


def test_blocking_removes_circle_connection_and_pending_requests():
    a, a_c = _person("Avery")
    b, b_c = _person("Blake")
    c, c_c = _person("Casey")
    db = SessionLocal()
    connect(db, uuid.UUID(a), uuid.UUID(b))
    db.commit()
    request_from_invite(db, uuid.UUID(a), uuid.UUID(c))
    db.close()

    _block(a_c, b)
    _block(c_c, a)
    assert client.get("/api/circle", cookies=a_c).json()["members"] == []
    assert client.get("/api/circle", cookies=b_c).json()["members"] == []
    assert client.get("/api/circle", cookies=c_c).json()["requests"] == []

    db = SessionLocal()
    request_from_invite(db, uuid.UUID(a), uuid.UUID(c))  # opening the blocked person's invite link again
    assert db.query(CircleRequest).filter(CircleRequest.to_user_id == uuid.UUID(c)).count() == 0
    db.close()


def test_no_friend_of_friend_introduction_through_someone_you_blocked():
    me, me_c = _person("Me")
    maya, _ = _person("Maya")
    blake, _ = _person("Blake")
    db = SessionLocal()
    connect(db, uuid.UUID(me), uuid.UUID(maya))
    connect(db, uuid.UUID(maya), uuid.UUID(blake))
    db.commit()
    db.close()
    _block(me_c, maya)
    intro = next(c["intro"] for c in client.get("/api/discover/candidates", cookies=me_c).json() if c["id"] == blake)
    assert "Maya" not in intro


def test_block_list_shows_only_people_you_blocked():
    a, a_c = _person("Avery")
    b, b_c = _person("Blake")
    _block(a_c, b)
    assert [p["first_name"] for p in client.get("/api/blocks", cookies=a_c).json()] == ["Blake"]
    assert client.get("/api/blocks", cookies=b_c).json() == [], "never reveals who blocked you"
    assert client.delete(f"/api/blocks/{a}", cookies=b_c).status_code == 404, "only the blocker can unblock"


def test_blocking_twice_is_harmless_and_self_block_is_rejected():
    a, a_c = _person("Avery")
    b, _ = _person("Blake")
    assert _block(a_c, b).status_code == 204
    assert _block(a_c, b).status_code == 204
    assert len(client.get("/api/blocks", cookies=a_c).json()) == 1
    assert _block(a_c, a).status_code == 400
    assert _block(a_c, str(uuid.uuid4())).status_code == 404


def test_reporting_records_the_report_and_blocks_by_default():
    a, a_c = _person("Avery")
    b, _ = _person("Blake")
    response = client.post("/api/reports", json={"user_id": b, "reason": "recruiting_or_referrals", "details": " kept pitching jobs "}, cookies=a_c)
    assert response.status_code == 201
    db = SessionLocal()
    report = db.query(UserReport).filter(UserReport.reported_id == uuid.UUID(b)).one()
    assert report.reason.value == "recruiting_or_referrals" and report.details == "kept pitching jobs"
    assert report.status.value == "open"
    db.close()
    assert b not in _feed(a_c)


def test_reporting_without_blocking():
    a, a_c = _person("Avery")
    b, _ = _person("Blake")
    client.post("/api/reports", json={"user_id": b, "reason": "spam", "also_block": False}, cookies=a_c)
    assert b in _feed(a_c)


def test_invalid_reports_are_rejected():
    a, a_c = _person("Avery")
    b, _ = _person("Blake")
    assert client.post("/api/reports", json={"user_id": b, "reason": "not_a_reason"}, cookies=a_c).status_code == 422
    assert client.post("/api/reports", json={"user_id": a, "reason": "spam"}, cookies=a_c).status_code == 400
    assert client.post("/api/reports", json={"user_id": b, "reason": "spam", "details": "x" * 2001}, cookies=a_c).status_code == 422


def test_safety_endpoints_require_sign_in():
    assert client.get("/api/blocks").status_code == 401
    assert client.post("/api/blocks", json={"user_id": str(uuid.uuid4())}).status_code == 401
    assert client.post("/api/reports", json={"user_id": str(uuid.uuid4()), "reason": "spam"}).status_code == 401


def test_the_block_alone_is_enough_even_if_both_still_want_to_connect():
    """Blocking also records a pass, which hides people on its own. This test
    removes that layer - a block row plus two people who both chose Connect -
    to prove the central block check separates them by itself."""
    from app.models.safety import UserBlock

    a, a_c = _person("Avery")
    b, b_c = _person("Blake")
    _connect(a_c, b)
    assert _connect(b_c, a).json()["matched"] is True
    db = SessionLocal()
    db.add(UserBlock(blocker_id=uuid.UUID(a), blocked_id=uuid.UUID(b)))
    db.commit()
    db.close()
    for cookies in (a_c, b_c):
        assert client.get("/api/matches", cookies=cookies).json() == []
    c, c_c = _person("Casey")
    d, d_c = _person("Dana")
    db = SessionLocal()
    db.add(UserBlock(blocker_id=uuid.UUID(c), blocked_id=uuid.UUID(d)))
    db.commit()
    db.close()
    assert d not in _feed(c_c) and c not in _feed(d_c)
