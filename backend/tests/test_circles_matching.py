"""
Circles in matching: people already in your circle leave Discovery, and
friends of friends rank higher with a "You both know Maya" intro - naming
only friends who allow it.
"""
import uuid

import pytest
from sqlalchemy import event

from app.db.session import Base, engine, SessionLocal
from app.models.user import User
from app.models.user_location import UserLocation
from app.services.circles import connect
from app.services.compatibility_scoring import get_ranked_candidates
from app.services.eligibility import get_eligible_candidates


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _person(db, name="Test", nameable=True):
    u = User(linkedin_sub=f"t-{uuid.uuid4()}", email=f"t-{uuid.uuid4()}@example.com", first_name=name, last_name="U",
             account_status="active", onboarding_completed=True, show_as_mutual_connection=nameable)
    db.add(u)
    db.flush()
    db.add(UserLocation(user_id=u.id, city="NYC", latitude=40.7128, longitude=-74.0060, travel_radius_miles=25, is_primary=True))
    db.commit()
    return u.id


def _friends(db, a, b):
    connect(db, a, b)
    db.commit()


def test_people_already_in_your_circle_leave_discovery():
    db = SessionLocal()
    me, friend, stranger = _person(db), _person(db, "Friend"), _person(db, "Stranger")
    _friends(db, me, friend)
    feed = [c.id for c in get_eligible_candidates(db, me)]
    assert friend not in feed and stranger in feed
    assert me not in [c.id for c in get_eligible_candidates(db, friend)], "works in both directions"
    db.close()


def test_a_friend_of_a_friend_ranks_higher_and_is_introduced_warmly():
    db = SessionLocal()
    me, maya = _person(db), _person(db, "Maya")
    fof, stranger = _person(db, "Blake"), _person(db, "Casey")
    _friends(db, me, maya)
    _friends(db, maya, fof)
    r = {sc.user.id: sc for sc in get_ranked_candidates(db, me)}
    assert r[fof].score - r[stranger].score == 4
    assert "both know Maya" in r[fof].intro
    assert "Maya" not in r[stranger].intro
    db.close()


def test_a_friend_who_opted_out_still_counts_but_is_never_named():
    db = SessionLocal()
    me, quiet = _person(db), _person(db, "Quinn", nameable=False)
    fof, stranger = _person(db, "Blake"), _person(db, "Casey")
    _friends(db, me, quiet)
    _friends(db, quiet, fof)
    r = {sc.user.id: sc for sc in get_ranked_candidates(db, me)}
    assert r[fof].score - r[stranger].score == 4, "still helps the match"
    assert "Quinn" not in r[fof].intro and not any("Quinn" in x for x in r[fof].reasons)
    db.close()


def test_several_mutual_friends_are_capped_and_summarized():
    db = SessionLocal()
    me, fof, stranger = _person(db), _person(db, "Blake"), _person(db, "Casey")
    for name in ("Ava", "Ben", "Cal", "Dee"):
        f = _person(db, name)
        _friends(db, me, f)
        _friends(db, f, fof)
    r = {sc.user.id: sc for sc in get_ranked_candidates(db, me)}
    assert r[fof].score - r[stranger].score == 12, "4 per mutual friend, counted up to 3"
    assert "both know Ava and Ben, among others" in r[fof].intro
    db.close()


def test_ranking_with_circles_stays_flat_as_candidates_grow():
    def scenario(n):
        db = SessionLocal()
        me = _person(db)
        for _ in range(n):
            friend, fof = _person(db, "F"), _person(db, "C")
            _friends(db, me, friend)
            _friends(db, friend, fof)
        db.close()
        return me

    def count(me):
        db = SessionLocal()
        n = 0

        def on_execute(*args, **kwargs):
            nonlocal n
            n += 1

        event.listen(db.bind, "before_cursor_execute", on_execute)
        try:
            get_ranked_candidates(db, me)
        finally:
            event.remove(db.bind, "before_cursor_execute", on_execute)
            db.close()
        return n

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    small = count(scenario(2))
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    large = count(scenario(8))
    assert small == large, f"2: {small} queries, 8: {large} - N+1 crept in"
