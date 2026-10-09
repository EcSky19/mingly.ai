"""
Tests for notification emails: who gets one, when, and - just as important -
when nobody does (a repeat action, notifications off, suspended or blocked
people). Also the SMTP sender itself: skipped without a host, never raises.

The send function is replaced with a recorder, so the routes, the
background-task wiring, and the decision logic are all real.
"""
import json
import smtplib
import uuid
from base64 import b64encode

import itsdangerous
import pytest
from fastapi.testclient import TestClient

from app.api.routes import circle as circle_routes
from app.api.routes import interactions as interaction_routes
from app.core.config import settings
from app.db.session import Base, engine, SessionLocal
from app.main import app
from app.models.user import User
from app.services import email as email_service
from app.services.circles import request_from_invite
from app.services.email import Email, send_email
from app.services.safety import block

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sent(monkeypatch):
    outbox: list[Email] = []
    monkeypatch.setattr(interaction_routes, "send_email", outbox.append)
    monkeypatch.setattr(circle_routes, "send_email", outbox.append)
    client.cookies.clear()
    return outbox


def _cookie_for(user_id: str) -> dict:
    signer = itsdangerous.TimestampSigner(settings.SESSION_SECRET)
    data = b64encode(json.dumps({"user_id": user_id}).encode("utf-8"))
    return {settings.SESSION_COOKIE_NAME: signer.sign(data).decode("utf-8")}


def _person(name="Test", **fields):
    db = SessionLocal()
    user = User(
        linkedin_sub=f"t-{uuid.uuid4()}", email=f"{name.lower()}-{uuid.uuid4().hex[:6]}@example.com",
        first_name=name, last_name="Private", onboarding_completed=True, **fields,
    )
    db.add(user)
    db.commit()
    out = (str(user.id), user.email, _cookie_for(str(user.id)))
    db.close()
    return out


def _act(cookies, target_id, action="interested"):
    r = client.post("/api/discover/interact", json={"target_user_id": target_id, "action": action}, cookies=cookies)
    assert r.status_code == 201, r.text
    return r.json()


def _set(user_id, **fields):
    db = SessionLocal()
    db.query(User).filter(User.id == uuid.UUID(user_id)).update(fields)
    db.commit()
    db.close()


# --- New match ---

def test_new_match_emails_the_person_who_said_connect_first(sent):
    ethan, ethan_email, ethan_c = _person("Ethan")
    maya, _, maya_c = _person("Maya")
    _act(ethan_c, maya)
    assert sent == [], "a one-sided Connect never notifies anyone"

    assert _act(maya_c, ethan)["matched"] is True
    assert len(sent) == 1
    email = sent[0]
    assert email.to == ethan_email
    assert email.subject == "You and Maya matched on Mingly"
    assert f"{settings.APP_URL}/matches" in email.text
    assert f"{settings.APP_URL}/settings" in email.text, "every email says how to turn them off"
    assert "Private" not in email.text + email.subject, "only first names, never last names"


def test_repeating_connect_on_an_existing_match_sends_nothing_new(sent):
    a, _, a_c = _person("Ana")
    b, _, b_c = _person("Ben")
    _act(a_c, b)
    _act(b_c, a)
    _act(b_c, a)
    _act(a_c, b)
    assert len(sent) == 1


def test_pass_and_decide_later_never_email(sent):
    a, _, a_c = _person("Ana")
    b, _, b_c = _person("Ben")
    _act(a_c, b)
    _act(b_c, a, "dismissed")
    _act(b_c, a, "later")
    assert sent == []


def test_no_email_when_the_recipient_turned_notifications_off(sent):
    a, _, a_c = _person("Ana", email_notifications=False)
    b, _, b_c = _person("Ben")
    _act(a_c, b)
    assert _act(b_c, a)["matched"] is True, "the match itself still happens"
    assert sent == []


def test_no_email_to_a_suspended_account(sent):
    a, _, a_c = _person("Ana")
    b, _, b_c = _person("Ben")
    _act(a_c, b)
    _set(a, account_status="suspended")
    _act(b_c, a)
    assert sent == []


# --- Circle joined ---

def _pending_request(inviter, invitee):
    db = SessionLocal()
    request_from_invite(db, uuid.UUID(inviter), uuid.UUID(invitee))
    db.close()


def test_accepting_a_circle_invite_emails_the_inviter(sent):
    ethan, ethan_email, _ = _person("Ethan")
    maya, _, maya_c = _person("Maya")
    _pending_request(ethan, maya)
    req = client.get("/api/circle", cookies=maya_c).json()["requests"][0]
    assert client.post(f"/api/circle/requests/{req['id']}/accept", cookies=maya_c).status_code == 204

    assert len(sent) == 1
    assert sent[0].to == ethan_email
    assert sent[0].subject == "Maya joined your circle on Mingly"
    assert f"{settings.APP_URL}/circle" in sent[0].text


def test_declining_a_circle_invite_sends_nothing(sent):
    ethan, _, _ = _person("Ethan")
    maya, _, maya_c = _person("Maya")
    _pending_request(ethan, maya)
    req = client.get("/api/circle", cookies=maya_c).json()["requests"][0]
    assert client.post(f"/api/circle/requests/{req['id']}/decline", cookies=maya_c).status_code == 204
    assert sent == []


def test_circle_email_respects_the_inviters_setting(sent):
    ethan, _, _ = _person("Ethan", email_notifications=False)
    maya, _, maya_c = _person("Maya")
    _pending_request(ethan, maya)
    req = client.get("/api/circle", cookies=maya_c).json()["requests"][0]
    assert client.post(f"/api/circle/requests/{req['id']}/accept", cookies=maya_c).status_code == 204
    assert sent == []


def test_blocked_people_never_trigger_an_email(sent):
    """Defense in depth: the notification check refuses blocked pairs even
    if some future route forgot its own block check."""
    from app.services.notifications import circle_joined_email, new_match_email
    a, _, _ = _person("Ana")
    b, _, _ = _person("Ben")
    db = SessionLocal()
    block(db, uuid.UUID(b), uuid.UUID(a))
    db.commit()
    assert new_match_email(db, uuid.UUID(a), uuid.UUID(b)) is None
    assert circle_joined_email(db, uuid.UUID(a), uuid.UUID(b)) is None
    db.close()


# --- Preferences ---

def test_email_notifications_preference_round_trips(sent):
    a, _, a_c = _person("Ana")
    assert client.get("/api/auth/me", cookies=a_c).json()["email_notifications"] is True
    r = client.put("/api/auth/preferences", json={"email_notifications": False}, cookies=a_c)
    assert r.status_code == 200 and r.json() == {"email_notifications": False}
    assert client.get("/api/auth/me", cookies=a_c).json()["email_notifications"] is False


def test_preferences_require_sign_in(sent):
    assert client.put("/api/auth/preferences", json={"email_notifications": False}).status_code == 401


# --- The SMTP sender ---

MSG = Email(to="x@example.com", subject="Hi", text="Body")


def test_without_an_smtp_host_emails_are_skipped(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    def boom(*a, **k):
        raise AssertionError("must not connect")
    monkeypatch.setattr(smtplib, "SMTP", boom)
    assert send_email(MSG) is False


def test_send_uses_starttls_and_login(monkeypatch):
    calls = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            calls.append(("connect", host, port))
        def starttls(self, context):
            calls.append(("starttls",))
        def login(self, user, pw):
            calls.append(("login", user, pw))
        def send_message(self, msg):
            calls.append(("send", msg["To"], msg["Subject"], msg["From"]))
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "user")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "pw")
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
    assert send_email(MSG) is True
    assert calls == [
        ("connect", "smtp.example.com", 587), ("starttls",), ("login", "user", "pw"),
        ("send", "x@example.com", "Hi", settings.EMAIL_FROM),
    ]


def test_a_mail_outage_never_raises(monkeypatch):
    def down(*a, **k):
        raise OSError("connection refused")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(email_service.smtplib, "SMTP", down)
    assert send_email(MSG) is False
