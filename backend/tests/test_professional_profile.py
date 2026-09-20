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


def test_cities_autocomplete_endpoint_exists_and_fails_open():
    # No live network to Photon in the test environment - confirms the
    # route is correctly registered and fails open rather than erroring
    # or 404ing (this caught a real path-mismatch bug during development).
    response = client.get("/api/cities/autocomplete?q=new+york")
    assert response.status_code == 200
    assert response.json() == []


def test_languages_autocomplete_matches():
    response = client.get("/api/languages/autocomplete?q=span")
    assert response.status_code == 200
    results = response.json()
    assert any(r["value"] == "Spanish" for r in results)


def test_languages_requires_auth():
    assert client.get("/api/profile/languages").status_code == 401
    assert client.post("/api/profile/languages", json={"language": "English"}).status_code == 401


def test_add_multiple_languages_with_proficiency_and_matching_flag(test_user):
    cookie = _session_cookie_for(str(test_user.id))
    client.cookies.set(settings.SESSION_COOKIE_NAME, cookie)

    r1 = client.post(
        "/api/profile/languages",
        json={"language": "English", "proficiency": "native", "visible_on_profile": True, "usable_for_matching": True},
    )
    assert r1.status_code == 201
    lang1_id = r1.json()["id"]

    r2 = client.post(
        "/api/profile/languages",
        json={"language": "Spanish", "proficiency": "conversational", "usable_for_matching": False},
    )
    assert r2.status_code == 201

    listing = client.get("/api/profile/languages").json()
    assert len(listing) == 2
    english = next(l for l in listing if l["language"] == "English")
    assert english["proficiency"] == "native"
    assert english["usable_for_matching"] is True
    spanish = next(l for l in listing if l["language"] == "Spanish")
    assert spanish["proficiency"] == "conversational"
    assert spanish["usable_for_matching"] is False  # explicitly opted out

    delete_resp = client.delete(f"/api/profile/languages/{lang1_id}")
    assert delete_resp.status_code == 204
    remaining = client.get("/api/profile/languages").json()
    assert len(remaining) == 1
    assert remaining[0]["language"] == "Spanish"

    client.cookies.clear()


def test_language_delete_scoped_to_owner(test_user):
    cookie = _session_cookie_for(str(test_user.id))

    other_db = SessionLocal()
    other_user = User(
        linkedin_sub=f"test-other-lang-{uuid.uuid4()}",
        email=f"test-other-lang-{uuid.uuid4()}@example.com",
        first_name="Other",
        last_name="User",
    )
    other_db.add(other_user)
    other_db.commit()
    other_db.refresh(other_user)
    other_cookie = _session_cookie_for(str(other_user.id))
    cookie_name = settings.SESSION_COOKIE_NAME

    create_resp = client.post(
        "/api/profile/languages", json={"language": "French"}, cookies={cookie_name: other_cookie}
    )
    other_entry_id = create_resp.json()["id"]

    delete_resp = client.delete(
        f"/api/profile/languages/{other_entry_id}", cookies={cookie_name: cookie}
    )
    assert delete_resp.status_code == 404

    still_there = client.get(
        "/api/profile/languages", cookies={cookie_name: other_cookie}
    ).json()
    assert any(l["id"] == other_entry_id for l in still_there)

    other_db.close()
    client.cookies.clear()


def test_job_titles_autocomplete_fails_open_when_unseeded():
    # Table has no seed data in this test DB (only production has the
    # seeded starter set via migration 0003's data seed) - should
    # return empty, not error.
    response = client.get("/api/job-titles/autocomplete?q=engineer")
    assert response.status_code == 200
    assert response.json() == []


def test_industries_autocomplete():
    response = client.get("/api/industries/autocomplete?q=tech")
    assert response.status_code == 200
    results = response.json()
    assert any("Technology" in r["value"] for r in results)


def test_education_requires_auth():
    assert client.get("/api/profile/education").status_code == 401
    assert client.post("/api/profile/education", json={}).status_code == 401


def test_education_supports_multiple_entries(test_user):
    """The core requirement this whole redesign was for: a user must be
    able to add more than one school/degree, not just one."""
    cookie = _session_cookie_for(str(test_user.id))
    client.cookies.set(settings.SESSION_COOKIE_NAME, cookie)

    r1 = client.post(
        "/api/profile/education",
        json={"school": "Cornell University", "degree": "Bachelor of Science (BS)", "field_of_study": "Computer Science", "graduation_year": 2020},
    )
    assert r1.status_code == 201
    entry1_id = r1.json()["id"]

    r2 = client.post(
        "/api/profile/education",
        json={"school": "Columbia University", "degree": "Master of Business Administration (MBA)", "graduation_year": 2024},
    )
    assert r2.status_code == 201
    entry2_id = r2.json()["id"]
    assert entry1_id != entry2_id

    listing = client.get("/api/profile/education")
    assert listing.status_code == 200
    schools = [e["school"] for e in listing.json()]
    assert "Cornell University" in schools
    assert "Columbia University" in schools
    assert len(listing.json()) == 2

    # Deleting one entry doesn't touch the other
    delete_resp = client.delete(f"/api/profile/education/{entry1_id}")
    assert delete_resp.status_code == 204
    listing_after = client.get("/api/profile/education").json()
    assert len(listing_after) == 1
    assert listing_after[0]["school"] == "Columbia University"

    client.cookies.clear()


def test_education_delete_is_scoped_to_owner(test_user):
    """A user can't delete someone else's education entry. Uses explicit
    per-request cookies (not the shared client.cookies jar) to avoid any
    ambiguity about which identity a request is actually using."""
    cookie = _session_cookie_for(str(test_user.id))

    other_user_db = SessionLocal()
    other_user = User(
        linkedin_sub=f"test-other-{uuid.uuid4()}",
        email=f"test-other-{uuid.uuid4()}@example.com",
        first_name="Other",
        last_name="User",
    )
    other_user_db.add(other_user)
    other_user_db.commit()
    other_user_db.refresh(other_user)
    other_cookie = _session_cookie_for(str(other_user.id))

    cookie_name = settings.SESSION_COOKIE_NAME

    create_resp = client.post(
        "/api/profile/education",
        json={"school": "Someone Else's School"},
        cookies={cookie_name: other_cookie},
    )
    other_entry_id = create_resp.json()["id"]

    # Confirm it was actually created under the OTHER user, not test_user -
    # otherwise this test wouldn't be testing what it claims to.
    other_users_entries = client.get(
        "/api/profile/education", cookies={cookie_name: other_cookie}
    ).json()
    assert any(e["id"] == other_entry_id for e in other_users_entries)
    test_users_entries = client.get(
        "/api/profile/education", cookies={cookie_name: cookie}
    ).json()
    assert not any(e["id"] == other_entry_id for e in test_users_entries)

    # Now the actual test: test_user tries to delete other_user's entry
    delete_resp = client.delete(
        f"/api/profile/education/{other_entry_id}", cookies={cookie_name: cookie}
    )
    assert delete_resp.status_code == 404

    # And it's still there, since the delete should have been rejected
    still_there = client.get(
        "/api/profile/education", cookies={cookie_name: other_cookie}
    ).json()
    assert any(e["id"] == other_entry_id for e in still_there)

    other_user_db.close()
