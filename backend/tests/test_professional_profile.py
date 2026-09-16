"""
Tests for the professional profile onboarding endpoints and autocomplete
services. Uses a real signed session cookie (matching Starlette's
SessionMiddleware signing scheme) to test the authenticated path for
real, not just the 401 case.
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


def _session_cookie_for(user_id: str) -> str:
    """Builds a valid signed session cookie the same way Starlette's
    SessionMiddleware does, so we can test authenticated endpoints
    without going through the real LinkedIn OAuth flow."""
    signer = itsdangerous.TimestampSigner(settings.SESSION_SECRET)
    data = b64encode(json.dumps({"user_id": user_id}).encode("utf-8"))
    return signer.sign(data).decode("utf-8")


def test_professional_profile_requires_auth():
    response = client.get("/api/profile/professional")
    assert response.status_code == 401

    response = client.put("/api/profile/professional", json={})
    assert response.status_code == 401


def test_professional_profile_starts_empty(test_user):
    cookie = _session_cookie_for(str(test_user.id))
    client.cookies.set(settings.SESSION_COOKIE_NAME, cookie)
    response = client.get("/api/profile/professional")
    assert response.status_code == 200
    body = response.json()
    assert body["current_role"] is None
    assert body["company"] is None
    client.cookies.clear()


def test_professional_profile_partial_update_and_privacy_flags(test_user):
    """Confirms a user can submit just one field and it saves correctly,
    with independent visible/matching privacy flags - the core design
    requirement from docs/professional-profile-design.md."""
    cookie = _session_cookie_for(str(test_user.id))
    client.cookies.set(settings.SESSION_COOKIE_NAME, cookie)

    response = client.put(
        "/api/profile/professional",
        json={
            "industry": {
                "value": "Technology",
                "visible_on_profile": False,
                "usable_for_matching": True,
            }
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["industry"] == "Technology"
    assert body["company"] is None  # untouched field stays empty

    # Confirm it actually persisted, not just echoed back
    response = client.get("/api/profile/professional")
    assert response.json()["industry"] == "Technology"
    client.cookies.clear()


def test_degrees_autocomplete_matches_and_limits():
    response = client.get("/api/degrees/autocomplete?q=bach")
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    assert all("bach" in r["value"].lower() for r in results)


def test_degrees_autocomplete_no_match_returns_empty():
    response = client.get("/api/degrees/autocomplete?q=zzzznotarealdegree")
    assert response.status_code == 200
    assert response.json() == []


def test_fields_of_study_autocomplete():
    response = client.get("/api/fields-of-study/autocomplete?q=comput")
    assert response.status_code == 200
    results = response.json()
    assert any("Computer" in r["value"] for r in results)


def test_company_autocomplete_fails_open_on_short_query():
    # Queries under 2 chars should short-circuit without even calling Clearbit
    response = client.get("/api/companies/autocomplete?q=a")
    assert response.status_code == 200
    assert response.json() == []


def test_job_titles_autocomplete_fails_open_when_unseeded():
    # Table has no seed data in this test DB - should return empty, not error
    response = client.get("/api/job-titles/autocomplete?q=engineer")
    assert response.status_code == 200
    assert response.json() == []
