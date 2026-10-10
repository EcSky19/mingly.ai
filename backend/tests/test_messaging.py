"""
Tests for messaging. The core guarantees: only current mutual matches and
circle members can message; friends of friends, strangers, and anyone
blocked (either direction) get the same 404 as a nonexistent person;
unmatching or blocking closes a conversation for both people at once;
one email per new conversation, never containing the message.
"""
import json
import uuid
from base64 import b64encode

import itsdangerous
import pytest
from fastapi.testclient import TestClient

from app.api.routes import messages as message_routes
from app.core.config import settings
from app.db.session import Base, engine, SessionLocal
from app.main import app
from app.models.user import User
from app.services import messaging
from app.services.circles import connect

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def outbox(monkeypatch):
    sent = []
    monkeypatch.setattr(message_routes, "send_email", sent.append)
    client.cookies.clear()
    return sent


class Person:
    def __init__(self, name="Test", **fields):
        db = SessionLocal()
        user = User(
            linkedin_sub=f"t-{uuid.uuid4()}", email=f"{name.lower()}-{uuid.uuid4().hex[:6]}@example.com",
            first_name=name, last_name="Private", onboarding_completed=True, **fields,
        )
        db.add(user)
        db.commit()
        self.id, self.email, self.name = str(user.id), user.email, name
        db.close()
        signer = itsdangerous.TimestampSigner(settings.SESSION_SECRET)
        data = b64encode(json.dumps({"user_id": self.id}).encode("utf-8"))
        self.cookies = {settings.SESSION_COOKIE_NAME: signer.sign(data).decode("utf-8")}

    def get(self, path, **kw):
        return client.get(path, cookies=self.cookies, **kw)

    def post(self, path, **kw):
        return client.post(path, cookies=self.cookies, **kw)

    def delete(self, path, **kw):
        return client.delete(path, cookies=self.cookies, **kw)

    def act(self, other, action="interested"):
        r = self.post("/api/discover/interact", json={"target_user_id": other.id, "action": action})
        assert r.status_code == 201, r.text

    def send(self, other, body="Hi!"):
        return self.post(f"/api/messages/with/{other.id}", json={"body": body})

    def thread(self, other, **params):
        return self.get(f"/api/messages/with/{other.id}", params=params)

    def inbox(self):
        r = self.get("/api/messages")
        assert r.status_code == 200, r.text
        return r.json()

    def unread(self):
        return self.get("/api/messages/unread").json()["conversations"]


def matched(a_name="Ana", b_name="Ben"):
    a, b = Person(a_name), Person(b_name)
    a.act(b)
    b.act(a)
    return a, b


def circle(a_name="Cara", b_name="Dev"):
    a, b = Person(a_name), Person(b_name)
    db = SessionLocal()
    connect(db, uuid.UUID(a.id), uuid.UUID(b.id))
    db.commit()
    db.close()
    return a, b


def set_status(person, status):
    db = SessionLocal()
    db.query(User).filter(User.id == uuid.UUID(person.id)).update({"account_status": status})
    db.commit()
    db.close()


# --- Who can message ---

def test_matches_can_message_each_other():
    a, b = matched()
    r = a.send(b, "  Coffee this week?  ")
    assert r.status_code == 201, r.text
    assert r.json()["body"] == "Coffee this week?" and r.json()["from_me"] is True
    assert b.send(a, "Yes - Thursday?").status_code == 201

    thread = b.thread(a).json()
    assert thread["relationship"] == "match"
    assert thread["person"]["first_name"] == "Ana"
    assert [(m["body"], m["from_me"]) for m in thread["messages"]] == [("Coffee this week?", False), ("Yes - Thursday?", True)]
    assert "Private" not in json.dumps(thread), "only first names, never last names"


def test_circle_members_can_message():
    a, b = circle()
    assert a.send(b).status_code == 201
    assert b.thread(a).json()["relationship"] == "circle"


def test_a_one_sided_connect_is_not_enough():
    a, b = Person("Ana"), Person("Ben")
    a.act(b)
    assert a.send(b).status_code == 404
    assert b.send(a).status_code == 404
    assert a.thread(b).status_code == 404


def test_friends_of_friends_cannot_message_directly():
    a, b = circle("Ana", "Ben")
    c = Person("Cy")
    db = SessionLocal()
    connect(db, uuid.UUID(b.id), uuid.UUID(c.id))
    db.commit()
    db.close()
    assert a.send(c).status_code == 404
    assert c.send(a).status_code == 404


def test_strangers_self_and_bad_ids_all_get_the_same_404():
    a, stranger = Person("Ana"), Person("Zed")
    for path in (f"/api/messages/with/{stranger.id}", f"/api/messages/with/{a.id}",
                 f"/api/messages/with/{uuid.uuid4()}", "/api/messages/with/not-a-uuid"):
        r = a.post(path, json={"body": "hi"})
        assert (r.status_code, r.json()) == (404, {"detail": "Conversation not found"}), path


def test_cannot_message_a_suspended_account_and_a_suspended_account_cannot_message():
    a, b = matched()
    set_status(b, "suspended")
    assert a.send(b).status_code == 404
    assert b.send(a).status_code == 403


def test_signed_out_requests_are_rejected():
    someone = Person()
    assert client.get("/api/messages").status_code == 401
    assert client.get("/api/messages/unread").status_code == 401
    assert client.post(f"/api/messages/with/{someone.id}", json={"body": "hi"}).status_code == 401


# --- Closing: unmatch and block ---

def test_unmatching_closes_the_conversation_for_both_and_a_rematch_reopens_it():
    a, b = matched()
    a.send(b, "first")
    assert a.delete(f"/api/matches/{b.id}").status_code == 204

    for me, other in ((a, b), (b, a)):
        assert me.inbox() == []
        assert me.thread(other).status_code == 404
        assert me.send(other).status_code == 404

    a.act(b)
    assert [m["body"] for m in b.thread(a).json()["messages"]] == ["first"], "history returns with the match"


def test_blocking_closes_it_in_both_directions_and_looks_like_nobody():
    a, b = matched()
    a.send(b, "hello")
    assert b.post("/api/blocks", json={"user_id": a.id}).status_code == 204

    for me, other in ((a, b), (b, a)):
        assert me.inbox() == [] and me.unread() == 0
        r = me.send(other)
        assert (r.status_code, r.json()) == (404, {"detail": "Conversation not found"})
        assert me.thread(other).status_code == 404

    assert b.delete(f"/api/blocks/{a.id}").status_code == 204
    assert a.send(b).status_code == 404, "unblocking never reopens a conversation"


def test_leaving_a_circle_closes_the_conversation():
    a, b = circle()
    a.send(b)
    assert a.delete(f"/api/circle/members/{b.id}").status_code == 204
    assert b.inbox() == [] and b.send(a).status_code == 404


# --- Inbox and unread ---

def test_inbox_lists_newest_first_with_previews_and_unread_counts():
    me = Person("Me")
    x, y = Person("Xia"), Person("Yan")
    for other in (x, y):
        me.act(other)
        other.act(me)
    x.send(me, "from x")
    y.send(me, "a" * 300)
    y.send(me, "latest from y")

    inbox = me.inbox()
    assert [c["person"]["first_name"] for c in inbox] == ["Yan", "Xia"]
    assert inbox[0]["last_message"]["body"] == "latest from y"
    assert [c["unread"] for c in inbox] == [2, 1]
    assert me.unread() == 2

    me.thread(y)
    assert me.unread() == 1
    assert [c["unread"] for c in me.inbox()] == [0, 1]
    assert y.unread() == 0, "your own messages are never unread to you"


def test_long_previews_are_shortened_in_the_inbox_only():
    a, b = matched()
    a.send(b, "word " * 100)
    preview = b.inbox()[0]["last_message"]["body"]
    assert len(preview) <= 141 and preview.endswith("…")
    assert len(b.thread(a).json()["messages"][0]["body"]) == len(("word " * 100).strip())


def test_a_match_with_no_messages_isnt_in_the_inbox_but_can_be_opened():
    a, b = matched()
    assert a.inbox() == []
    r = a.thread(b)
    assert r.status_code == 200 and r.json()["messages"] == []


# --- Validation and limits ---

def test_empty_and_overlong_messages_are_rejected():
    a, b = matched()
    assert a.send(b, "   ").status_code == 422
    assert a.send(b, "").status_code == 422
    assert a.send(b, "x" * 2001).status_code == 422
    assert a.send(b, "x" * 2000).status_code == 201


def test_sending_too_fast_is_slowed_down(monkeypatch):
    monkeypatch.setattr(messaging, "RATE_LIMIT_MESSAGES", 3)
    a, b = matched()
    assert [a.send(b).status_code for _ in range(4)] == [201, 201, 201, 429]
    assert b.send(a).status_code == 201, "the limit is per sender"


def test_older_messages_page_in(monkeypatch):
    monkeypatch.setattr(message_routes, "PAGE_SIZE", 5)
    a, b = matched()
    for i in range(8):
        a.send(b, f"m{i}")
    page = b.thread(a).json()
    assert [m["body"] for m in page["messages"]] == ["m3", "m4", "m5", "m6", "m7"] and page["has_more"] is True
    older = b.thread(a, before=page["messages"][0]["id"]).json()
    assert [m["body"] for m in older["messages"]] == ["m0", "m1", "m2"] and older["has_more"] is False
    assert b.thread(a, before=str(uuid.uuid4())).status_code == 400


# --- Email ---

def test_one_email_per_new_conversation_without_the_message(outbox):
    a, b = matched("Ana", "Ben")
    a.send(b, "my secret plan")
    a.send(b, "second")
    b.send(a, "reply")
    assert len(outbox) == 1
    email = outbox[0]
    assert email.to == b.email
    assert email.subject == "Ana sent you a message on Mingly"
    assert f"{settings.APP_URL}/messages/{a.id}" in email.text
    assert "secret" not in email.text + email.subject


def test_no_email_when_notifications_are_off(outbox):
    a, b = Person("Ana"), Person("Ben", email_notifications=False)
    a.act(b)
    b.act(a)
    assert a.send(b).status_code == 201
    assert outbox == []


def test_the_block_alone_closes_it_even_while_the_match_is_still_intact():
    """A block also unmatches - so insert the block row by itself to prove
    messaging checks blocks directly, not just the side effects."""
    from app.models.safety import UserBlock
    a, b = matched()
    a.send(b, "hi")
    db = SessionLocal()
    db.add(UserBlock(blocker_id=uuid.UUID(b.id), blocked_id=uuid.UUID(a.id)))
    db.commit()
    db.close()
    assert a.send(b).status_code == 404
    assert a.thread(b).status_code == 404
    assert a.inbox() == [] and b.inbox() == []


def test_the_block_alone_closes_a_circle_conversation_too():
    from app.models.safety import UserBlock
    a, b = circle()
    a.send(b, "hi")
    db = SessionLocal()
    db.add(UserBlock(blocker_id=uuid.UUID(a.id), blocked_id=uuid.UUID(b.id)))
    db.commit()
    db.close()
    assert b.send(a).status_code == 404
    assert a.inbox() == [] and b.inbox() == []
