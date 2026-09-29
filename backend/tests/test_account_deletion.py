"""
Tests for account deletion. The full cascade-across-every-table
verification (locations, education, social profile, photos, both
interaction directions, disk cleanup, other accounts unaffected) was
manually verified against real Postgres - see the commit message. These
tests cover the endpoint's own behavior: auth, session clearing, and
that it actually removes the row.
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


def _cookie_for(user_id: str) -> dict:
    signer = itsdangerous.TimestampSigner(settings.SESSION_SECRET)
    data = b64encode(json.dumps({"user_id": user_id}).encode("utf-8"))
    return {settings.SESSION_COOKIE_NAME: signer.sign(data).decode("utf-8")}


def test_delete_account_requires_auth():
    assert client.delete("/api/auth/account").status_code == 401


def test_delete_account_removes_the_user_row():
    db = SessionLocal()
    user = User(
        linkedin_sub=f"test-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        first_name="Test",
        last_name="User",
    )
    db.add(user)
    db.commit()
    user_id = str(user.id)
    db.close()

    cookies = _cookie_for(user_id)
    response = client.delete("/api/auth/account", cookies=cookies)
    assert response.status_code == 200
    assert response.json()["ok"] is True

    db2 = SessionLocal()
    assert db2.query(User).filter(User.id == uuid.UUID(user_id)).first() is None
    db2.close()


def test_delete_account_clears_session():
    db = SessionLocal()
    user = User(
        linkedin_sub=f"test-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        first_name="Test",
        last_name="User",
    )
    db.add(user)
    db.commit()
    user_id = str(user.id)
    db.close()

    cookies = _cookie_for(user_id)
    client.delete("/api/auth/account", cookies=cookies)

    # The same session should no longer authenticate anything, since
    # the deleted user no longer exists to look up.
    response = client.get("/api/auth/me", cookies=cookies)
    assert response.status_code == 401


def test_deleting_one_account_does_not_affect_another():
    db = SessionLocal()
    a = User(linkedin_sub=f"test-{uuid.uuid4()}", email=f"test-{uuid.uuid4()}@example.com", first_name="A", last_name="User")
    b = User(linkedin_sub=f"test-{uuid.uuid4()}", email=f"test-{uuid.uuid4()}@example.com", first_name="B", last_name="User")
    db.add_all([a, b])
    db.commit()
    a_id, b_id = str(a.id), str(b.id)
    db.close()

    cookies_a = _cookie_for(a_id)
    client.delete("/api/auth/account", cookies=cookies_a)

    db2 = SessionLocal()
    assert db2.query(User).filter(User.id == uuid.UUID(b_id)).first() is not None
    db2.close()
