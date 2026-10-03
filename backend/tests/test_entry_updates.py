"""
Tests for editing saved multi-entry profile sections (locations,
education, languages, pets). None of these could be edited before - the
API had no update route, so the onboarding page silently dropped every
edit to a saved entry, including privacy-toggle changes. Each endpoint
gets the same guarantees checked: auth required, partial update (omitted
fields untouched), owner-scoped, explicit null on NOT NULL fields
rejected with a 422.
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

# section -> (create payload, an edit, a field that must stay untouched, a NOT NULL field)
SECTIONS = {
    "locations": ({"city": "New York", "latitude": 40.71, "longitude": -74.0, "is_primary": True},
                  {"travel_radius_miles": 8, "label": "Home"}, "city", "is_primary"),
    "education": ({"school": "Cornell", "visible_on_profile": True},
                  {"visible_on_profile": False}, "school", "visible_on_profile"),
    "languages": ({"language": "Spanish", "proficiency": "conversational", "visible_on_profile": True},
                  {"proficiency": "fluent"}, "language", "language"),
    "pets": ({"pet_type": "dog", "name": "Milo", "visible_on_profile": True},
             {"name": "Milo Jr", "size": "medium"}, "pet_type", "pet_type"),
}


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


def _new_user_cookies() -> dict:
    db = SessionLocal()
    user = User(linkedin_sub=f"t-{uuid.uuid4()}", email=f"t-{uuid.uuid4()}@example.com", first_name="T", last_name="U")
    db.add(user)
    db.commit()
    user_id = str(user.id)
    db.close()
    return _cookie_for(user_id)


def _create(section, cookies):
    payload = SECTIONS[section][0]
    response = client.post(f"/api/profile/{section}", json=payload, cookies=cookies)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.parametrize("section", SECTIONS)
def test_update_requires_auth(section):
    assert client.patch(f"/api/profile/{section}/{uuid.uuid4()}", json={}).status_code == 401


@pytest.mark.parametrize("section", SECTIONS)
def test_edit_to_a_saved_entry_persists_and_leaves_other_fields_alone(section):
    _, edit, untouched_field, _ = SECTIONS[section]
    cookies = _new_user_cookies()
    created = _create(section, cookies)

    response = client.patch(f"/api/profile/{section}/{created['id']}", json=edit, cookies=cookies)
    assert response.status_code == 200, response.text
    updated = response.json()
    for field, value in edit.items():
        assert updated[field] == value
    assert updated[untouched_field] == created[untouched_field]

    listed = next(e for e in client.get(f"/api/profile/{section}", cookies=cookies).json() if e["id"] == created["id"])
    for field, value in edit.items():
        assert listed[field] == value, "edit didn't actually persist"


@pytest.mark.parametrize("section", SECTIONS)
def test_explicit_null_on_a_required_field_is_rejected(section):
    not_null_field = SECTIONS[section][3]
    cookies = _new_user_cookies()
    created = _create(section, cookies)
    response = client.patch(f"/api/profile/{section}/{created['id']}", json={not_null_field: None}, cookies=cookies)
    assert response.status_code == 422


@pytest.mark.parametrize("section", SECTIONS)
def test_cannot_edit_another_users_entry(section):
    _, edit, _, _ = SECTIONS[section]
    owner_cookies, other_cookies = _new_user_cookies(), _new_user_cookies()
    created = _create(section, owner_cookies)

    response = client.patch(f"/api/profile/{section}/{created['id']}", json=edit, cookies=other_cookies)
    assert response.status_code == 404
    still = next(e for e in client.get(f"/api/profile/{section}", cookies=owner_cookies).json() if e["id"] == created["id"])
    for field in edit:
        assert still[field] == created[field], "another user's edit leaked through"


def test_making_a_location_primary_unmarks_the_old_primary():
    cookies = _new_user_cookies()
    first = client.post("/api/profile/locations", json={"city": "New York", "is_primary": True}, cookies=cookies).json()
    second = client.post("/api/profile/locations", json={"city": "Ithaca", "is_primary": False}, cookies=cookies).json()

    client.patch(f"/api/profile/locations/{second['id']}", json={"is_primary": True}, cookies=cookies)
    primary = {loc["city"]: loc["is_primary"] for loc in client.get("/api/profile/locations", cookies=cookies).json()}
    assert primary == {"New York": False, "Ithaca": True}
    assert first["id"] != second["id"]
