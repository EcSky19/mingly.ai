"""
Admin moderation: only admins can reach it (everyone else gets a plain 404),
reports can be reviewed and resolved, accounts can be suspended, unsuspended,
or banned - with immediate effect - and every action is audited.
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
from app.models.safety import AdminAction
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


def _person(name="Test", admin=False):
    db = SessionLocal()
    u = User(linkedin_sub=f"t-{uuid.uuid4()}", email=f"t-{uuid.uuid4()}@example.com", first_name=name, last_name="U",
             account_status="active", onboarding_completed=True, is_admin=admin)
    db.add(u)
    db.commit()
    uid = str(u.id)
    db.close()
    signer = itsdangerous.TimestampSigner(settings.SESSION_SECRET)
    return uid, {settings.SESSION_COOKIE_NAME: signer.sign(b64encode(json.dumps({"user_id": uid}).encode())).decode()}


def _report(reporter_cookies, reported_id, reason="spam"):
    client.post("/api/reports", json={"user_id": reported_id, "reason": reason, "details": "d"}, cookies=reporter_cookies)


@pytest.mark.parametrize("method,path", [
    ("get", "/api/admin/reports"),
    ("post", f"/api/admin/reports/{uuid.uuid4()}/dismiss"),
    ("post", f"/api/admin/users/{uuid.uuid4()}/status"),
])
def test_non_admins_get_a_plain_404(method, path):
    _, cookies = _person()
    if method == "get":
        response = client.get(path, cookies=cookies)
    else:
        response = client.post(path, json={"status": "banned"} if path.endswith("/status") else {}, cookies=cookies)
    assert response.status_code == 404


def test_me_says_whether_you_are_an_admin():
    _, admin_c = _person("Admin", admin=True)
    _, user_c = _person()
    assert client.get("/api/auth/me", cookies=admin_c).json()["is_admin"] is True
    assert client.get("/api/auth/me", cookies=user_c).json()["is_admin"] is False


def test_admin_sees_open_reports_with_context():
    _, admin_c = _person("Admin", admin=True)
    _, rep_c = _person("Reporter")
    bad, _ = _person("Spammer")
    _, rep2_c = _person("Reporter2")
    _report(rep_c, bad, "spam")
    _report(rep2_c, bad, "harassment")
    mine = [r for r in client.get("/api/admin/reports", cookies=admin_c).json() if r["reported"]["id"] == bad]
    assert {r["reason"] for r in mine} == {"spam", "harassment"}
    assert all(r["reports_against_reported"] == 2 for r in mine)
    assert all(r["reporter"]["first_name"].startswith("Reporter") for r in mine)


def test_suspending_takes_effect_immediately_and_resolves_the_report():
    admin, admin_c = _person("Admin", admin=True)
    _, rep_c = _person("Reporter")
    bad, bad_c = _person("Spammer")
    _report(rep_c, bad)
    report_id = next(r["id"] for r in client.get("/api/admin/reports", cookies=admin_c).json() if r["reported"]["id"] == bad)

    assert client.get("/api/auth/me", cookies=bad_c).status_code == 200
    r = client.post(f"/api/admin/users/{bad}/status", json={"status": "suspended", "note": "spam", "report_id": report_id}, cookies=admin_c)
    assert r.status_code == 200
    assert client.get("/api/auth/me", cookies=bad_c).status_code == 403, "suspension applies to an existing session"
    assert report_id not in [x["id"] for x in client.get("/api/admin/reports", cookies=admin_c).json()]
    actioned = next(x for x in client.get("/api/admin/reports?status=actioned", cookies=admin_c).json() if x["id"] == report_id)
    assert actioned["admin_note"] == "spam"

    client.post(f"/api/admin/users/{bad}/status", json={"status": "active"}, cookies=admin_c)
    assert client.get("/api/auth/me", cookies=bad_c).status_code == 200, "unsuspending restores access"

    db = SessionLocal()
    actions = [a.action for a in db.query(AdminAction).filter(AdminAction.target_user_id == uuid.UUID(bad)).order_by(AdminAction.created_at)]
    assert actions == ["suspend", "unsuspend"]
    assert all(a.admin_id == uuid.UUID(admin) for a in db.query(AdminAction).filter(AdminAction.target_user_id == uuid.UUID(bad)))
    db.close()


def test_a_banned_or_suspended_person_disappears_from_discover():
    _, admin_c = _person("Admin", admin=True)
    _, viewer_c = _person("Viewer")
    bad, _ = _person("Bad")
    from app.models.user_location import UserLocation
    db = SessionLocal()
    for u in db.query(User).filter(User.first_name.in_(["Viewer", "Bad"])).all():
        db.add(UserLocation(user_id=u.id, city="NYC", latitude=40.71, longitude=-74.0, travel_radius_miles=25, is_primary=True))
    db.commit()
    db.close()
    assert bad in [c["id"] for c in client.get("/api/discover/candidates", cookies=viewer_c).json()]
    client.post(f"/api/admin/users/{bad}/status", json={"status": "banned"}, cookies=admin_c)
    assert bad not in [c["id"] for c in client.get("/api/discover/candidates", cookies=viewer_c).json()]


def test_dismissing_a_report_is_audited():
    _, admin_c = _person("Admin", admin=True)
    _, rep_c = _person("Reporter")
    other, other_c = _person("Fine")
    _report(rep_c, other, "other")
    report_id = next(r["id"] for r in client.get("/api/admin/reports", cookies=admin_c).json() if r["reported"]["id"] == other)
    assert client.post(f"/api/admin/reports/{report_id}/dismiss", json={"note": "no issue"}, cookies=admin_c).status_code == 200
    assert client.get("/api/auth/me", cookies=other_c).status_code == 200, "dismissing doesn't affect the account"
    db = SessionLocal()
    assert db.query(AdminAction).filter(AdminAction.report_id == uuid.UUID(report_id)).one().action == "dismiss_report"
    db.close()


def test_admins_cannot_change_their_own_status_or_mismatch_a_report():
    admin, admin_c = _person("Admin", admin=True)
    _, rep_c = _person("Reporter")
    a, _ = _person("A")
    b, _ = _person("B")
    assert client.post(f"/api/admin/users/{admin}/status", json={"status": "banned"}, cookies=admin_c).status_code == 400
    _report(rep_c, a)
    report_id = next(r["id"] for r in client.get("/api/admin/reports", cookies=admin_c).json() if r["reported"]["id"] == a)
    assert client.post(f"/api/admin/users/{b}/status", json={"status": "suspended", "report_id": report_id}, cookies=admin_c).status_code == 400
    assert client.post(f"/api/admin/users/{b}/status", json={"status": "deleted"}, cookies=admin_c).status_code == 422
