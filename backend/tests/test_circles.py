"""
Tests for Circles: invite links carried through LinkedIn sign-in, accepting
and declining requests, removing members, and the public invite page.

Only LinkedIn's two network calls (code exchange, profile fetch) are stood
in for; the sign-in route, session handling, and invite logic are real. Each
person gets their own TestClient, i.e. their own browser cookie jar.
"""
import uuid
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app.db.session import Base, engine, SessionLocal
from app.main import app
from app.models.circle import CircleConnection
from app.models.user import User
from app.services import linkedin_auth


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def fake_linkedin(monkeypatch):
    """LinkedIn's network calls, stood in for. The 'code' we pass to the
    callback carries which person is signing in."""
    async def exchange(code):
        return f"token-for-{code}"

    async def userinfo(token):
        sub = token.removeprefix("token-for-")
        return {"sub": sub, "email": f"{sub}@example.com", "given_name": sub.split("-")[0].title(), "family_name": "T"}

    monkeypatch.setattr(linkedin_auth, "exchange_code_for_token", exchange)
    monkeypatch.setattr(linkedin_auth, "fetch_userinfo", userinfo)


def sign_in(name: str, invite: str | None = None) -> TestClient:
    """A fresh browser signs in through LinkedIn, optionally via an invite link."""
    browser = TestClient(app)
    login = browser.get("/api/auth/linkedin/login", params={"invite": invite} if invite else {}, follow_redirects=False)
    state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]
    callback = browser.get("/api/auth/linkedin/callback", params={"code": name, "state": state}, follow_redirects=False)
    assert callback.status_code in (302, 307), callback.text
    return browser


def new_name(label: str) -> str:
    return f"{label}-{uuid.uuid4().hex[:8]}"


def me(browser) -> dict:
    return browser.get("/api/auth/me").json()


def invite_code(browser) -> str:
    return browser.get("/api/circle/invite-link").json()["code"]


def test_invite_link_flow_connects_both_people_after_they_accept():
    ethan = sign_in(new_name("ethan"))
    link = ethan.get("/api/circle/invite-link").json()
    assert link["url"].endswith(f"/invite/{link['code']}")

    maya = sign_in(new_name("maya"), invite=link["code"])
    circle = maya.get("/api/circle").json()
    assert circle["members"] == []
    assert len(circle["requests"]) == 1
    req = circle["requests"][0]
    assert req["from_user"]["id"] == me(ethan)["id"]

    assert maya.post(f"/api/circle/requests/{req['id']}/accept").status_code == 204
    assert [m["id"] for m in maya.get("/api/circle").json()["members"]] == [me(ethan)["id"]]
    assert [m["id"] for m in ethan.get("/api/circle").json()["members"]] == [me(maya)["id"]], "circles are mutual"
    assert maya.get("/api/circle").json()["requests"] == []


def test_an_existing_user_signing_in_through_an_invite_also_gets_the_request():
    sam_name = new_name("sam")
    sign_in(sam_name)  # already has an account
    ethan = sign_in(new_name("ethan"))
    sam = sign_in(sam_name, invite=invite_code(ethan))
    assert len(sam.get("/api/circle").json()["requests"]) == 1


def test_declining_connects_no_one():
    ethan = sign_in(new_name("ethan"))
    maya = sign_in(new_name("maya"), invite=invite_code(ethan))
    req_id = maya.get("/api/circle").json()["requests"][0]["id"]
    assert maya.post(f"/api/circle/requests/{req_id}/decline").status_code == 204
    assert maya.get("/api/circle").json() | {"show_as_mutual_connection": None} == {
        "members": [], "requests": [], "show_as_mutual_connection": None,
    }
    assert ethan.get("/api/circle").json()["members"] == []


def test_opening_your_own_link_or_a_friends_again_creates_no_extra_request():
    ethan_name = new_name("ethan")
    ethan = sign_in(ethan_name)
    code = invite_code(ethan)
    ethan_again = sign_in(ethan_name, invite=code)
    assert ethan_again.get("/api/circle").json()["requests"] == [], "no request to yourself"

    maya_name = new_name("maya")
    maya = sign_in(maya_name, invite=code)
    maya.post(f"/api/circle/requests/{maya.get('/api/circle').json()['requests'][0]['id']}/accept")
    maya_again = sign_in(maya_name, invite=code)
    assert maya_again.get("/api/circle").json()["requests"] == [], "already connected"


def test_an_unknown_invite_code_is_ignored_and_sign_in_still_works():
    browser = sign_in(new_name("lee"), invite="doesnotexist")
    assert me(browser)["first_name"] == "Lee"
    assert browser.get("/api/circle").json()["requests"] == []


def test_only_the_recipient_can_answer_a_request():
    ethan = sign_in(new_name("ethan"))
    maya = sign_in(new_name("maya"), invite=invite_code(ethan))
    req_id = maya.get("/api/circle").json()["requests"][0]["id"]
    assert ethan.post(f"/api/circle/requests/{req_id}/accept").status_code == 404
    assert ethan.get("/api/circle").json()["members"] == []


def test_removing_someone_removes_the_connection_for_both():
    ethan = sign_in(new_name("ethan"))
    maya = sign_in(new_name("maya"), invite=invite_code(ethan))
    maya.post(f"/api/circle/requests/{maya.get('/api/circle').json()['requests'][0]['id']}/accept")
    assert ethan.delete(f"/api/circle/members/{me(maya)['id']}").status_code == 204
    assert ethan.get("/api/circle").json()["members"] == []
    assert maya.get("/api/circle").json()["members"] == []
    assert ethan.delete(f"/api/circle/members/{me(maya)['id']}").status_code == 404


def test_public_invite_page_shows_only_first_name_and_photo():
    ethan = sign_in(new_name("ethan"))
    info = TestClient(app).get(f"/api/invites/{invite_code(ethan)}")  # not signed in
    assert info.status_code == 200
    assert set(info.json()) == {"inviter_first_name", "inviter_photo_url"}
    assert info.json()["inviter_first_name"] == "Ethan"
    assert TestClient(app).get("/api/invites/doesnotexist").status_code == 404


def test_mutual_connection_setting_is_saved():
    browser = sign_in(new_name("ethan"))
    assert browser.get("/api/circle").json()["show_as_mutual_connection"] is True
    browser.put("/api/circle/settings", json={"show_as_mutual_connection": False})
    assert browser.get("/api/circle").json()["show_as_mutual_connection"] is False


def test_circle_endpoints_require_sign_in():
    anonymous = TestClient(app)
    assert anonymous.get("/api/circle").status_code == 401
    assert anonymous.get("/api/circle/invite-link").status_code == 401


def test_a_connection_is_stored_once_in_canonical_order():
    ethan = sign_in(new_name("ethan"))
    maya = sign_in(new_name("maya"), invite=invite_code(ethan))
    maya.post(f"/api/circle/requests/{maya.get('/api/circle').json()['requests'][0]['id']}/accept")
    a, b = uuid.UUID(me(ethan)["id"]), uuid.UUID(me(maya)["id"])
    db = SessionLocal()
    rows = db.query(CircleConnection).filter(
        CircleConnection.user_a_id.in_([a, b]), CircleConnection.user_b_id.in_([a, b])
    ).all()
    assert len(rows) == 1 and rows[0].user_a_id < rows[0].user_b_id
    db.close()
