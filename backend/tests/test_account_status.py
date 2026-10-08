"""
Suspended and banned accounts can't use the app. They can still delete
their account (people always keep the right to remove their data) and
log out.
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


def _user(status):
    db = SessionLocal()
    u = User(linkedin_sub=f"t-{uuid.uuid4()}", email=f"t-{uuid.uuid4()}@example.com", first_name="T", last_name="U",
             account_status=status, onboarding_completed=True)
    db.add(u)
    db.commit()
    uid = str(u.id)
    db.close()
    signer = itsdangerous.TimestampSigner(settings.SESSION_SECRET)
    return uid, {settings.SESSION_COOKIE_NAME: signer.sign(b64encode(json.dumps({"user_id": uid}).encode())).decode()}


@pytest.mark.parametrize("status", ["suspended", "banned"])
@pytest.mark.parametrize("path", ["/api/auth/me", "/api/discover/candidates", "/api/matches", "/api/circle", "/api/profile/social"])
def test_inactive_accounts_are_locked_out(status, path):
    _, cookies = _user(status)
    response = client.get(path, cookies=cookies)
    assert response.status_code == 403, f"{status} account could use {path}"


@pytest.mark.parametrize("status", ["suspended", "banned"])
def test_inactive_accounts_can_still_delete_their_account(status):
    uid, cookies = _user(status)
    assert client.delete("/api/auth/account", cookies=cookies).status_code == 200
    db = SessionLocal()
    assert db.query(User).filter(User.id == uuid.UUID(uid)).first() is None
    db.close()


def test_active_accounts_are_unaffected():
    _, cookies = _user("active")
    assert client.get("/api/auth/me", cookies=cookies).status_code == 200
