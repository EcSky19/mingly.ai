"""
Tests for app/services/public_profile.py - what one user may see about
another on a Discovery card. The core guarantee: nothing a person marked
not-visible-on-profile ever appears, directly or indirectly.
"""
import json
import uuid

import pytest
from sqlalchemy import event

from app.db.session import Base, engine, SessionLocal
from app.models.activity import Activity, UserActivity
from app.models.interest import Interest, UserInterest
from app.models.professional_profile import ProfessionalProfile
from app.models.user import User
from app.models.user_photo import UserPhoto
from app.services.public_profile import build_public_cards


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _make_user(db, photo=None):
    user = User(
        linkedin_sub=f"test-{uuid.uuid4()}",
        email=f"test-{uuid.uuid4()}@example.com",
        first_name="Test",
        last_name="User",
        profile_photo_url=photo,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _activity(db, label):
    a = Activity(id=uuid.uuid4(), name=f"{label} {uuid.uuid4()}", category="sports")
    db.add(a)
    db.commit()
    return a


def _interest(db, label):
    i = Interest(id=uuid.uuid4(), name=f"{label} {uuid.uuid4()}")
    db.add(i)
    db.commit()
    return i


def _professional(db, user_id, **fields):
    defaults = dict(user_id=user_id)
    defaults.update(fields)
    db.add(ProfessionalProfile(**defaults))
    db.commit()


def test_headline_uses_only_visible_fields():
    db = SessionLocal()
    user = _make_user(db)
    _professional(
        db, user.id,
        current_role="Engineer", current_role_visible_on_profile=True,
        company="SecretCorp", company_visible_on_profile=False,
        industry="Tech", industry_visible_on_profile=True,
    )
    card = build_public_cards(db, [user])[user.id]
    assert card.headline == "Engineer · Tech"
    db.close()


def test_no_headline_when_everything_professional_is_hidden():
    """Professional fields default to hidden - the default state should
    show no headline at all, not leak anything."""
    db = SessionLocal()
    user = _make_user(db)
    _professional(db, user.id, current_role="Engineer", company="Acme", industry="Tech")
    card = build_public_cards(db, [user])[user.id]
    assert card.headline is None
    db.close()


def test_hidden_activities_and_interests_never_appear():
    db = SessionLocal()
    user = _make_user(db)
    shown = _activity(db, "Shown")
    hidden = _activity(db, "Hidden")
    hidden_interest = _interest(db, "HiddenInterest")
    db.add(UserActivity(user_id=user.id, activity_id=shown.id, is_top_pick=True, visible_on_profile=True))
    db.add(UserActivity(user_id=user.id, activity_id=hidden.id, is_top_pick=True, visible_on_profile=False))
    db.add(UserInterest(user_id=user.id, interest_id=hidden_interest.id, is_top_pick=True, visible_on_profile=False))
    db.commit()

    card = build_public_cards(db, [user])[user.id]
    assert [a.name for a in card.activities] == [shown.name]
    assert card.interests == []
    db.close()


def test_photo_tagged_to_a_hidden_activity_does_not_show_the_tag():
    """An indirect leak path: the photo itself is fine to show, but its
    tag would name an activity the person hid."""
    db = SessionLocal()
    user = _make_user(db)
    shown = _activity(db, "Shown")
    hidden = _activity(db, "Hidden")
    db.add(UserActivity(user_id=user.id, activity_id=shown.id, is_top_pick=True, visible_on_profile=True))
    db.add(UserActivity(user_id=user.id, activity_id=hidden.id, is_top_pick=True, visible_on_profile=False))
    db.add(UserPhoto(user_id=user.id, file_path="photos/x/1.jpg", display_order=0, tagged_activity_id=shown.id))
    db.add(UserPhoto(user_id=user.id, file_path="photos/x/2.jpg", display_order=1, tagged_activity_id=hidden.id))
    db.commit()

    card = build_public_cards(db, [user])[user.id]
    assert [p.tag for p in card.photos] == [shown.name, None]
    assert hidden.name not in json.dumps([p.tag for p in card.photos])
    db.close()


def test_loved_items_listed_before_liked():
    db = SessionLocal()
    user = _make_user(db)
    liked = _activity(db, "Aaa-liked")
    loved = _activity(db, "Zzz-loved")
    db.add(UserActivity(user_id=user.id, activity_id=liked.id, is_top_pick=False, visible_on_profile=True))
    db.add(UserActivity(user_id=user.id, activity_id=loved.id, is_top_pick=True, visible_on_profile=True))
    db.commit()

    card = build_public_cards(db, [user])[user.id]
    assert [a.loved for a in card.activities] == [True, False]
    db.close()


def test_photo_url_handles_both_stored_shapes():
    db = SessionLocal()
    ours = _make_user(db, photo="linkedin/abc.jpg")
    legacy = _make_user(db, photo="https://media.licdn.com/x.jpg?e=1")
    cards = build_public_cards(db, [ours, legacy])
    assert cards[ours.id].photo_url == "/api/uploads/linkedin/abc.jpg"
    assert cards[legacy.id].photo_url == "https://media.licdn.com/x.jpg?e=1"
    db.close()


def test_card_building_query_count_is_flat():
    """Proves the batch-fetching holds: building cards for 2 people and
    for 8 people must execute the same number of SQL statements."""
    def _scenario(n):
        db = SessionLocal()
        users = []
        for _ in range(n):
            u = _make_user(db)
            act = _activity(db, "Act")
            db.add(UserActivity(user_id=u.id, activity_id=act.id, is_top_pick=True, visible_on_profile=True))
            db.add(UserPhoto(user_id=u.id, file_path="photos/x/1.jpg", display_order=0, tagged_activity_id=act.id))
            db.commit()
            users.append(u.id)
        db.close()
        return users

    def _count(user_ids):
        db = SessionLocal()
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        count = 0

        def _on_execute(*args, **kwargs):
            nonlocal count
            count += 1

        event.listen(db.bind, "before_cursor_execute", _on_execute)
        try:
            build_public_cards(db, users)
        finally:
            event.remove(db.bind, "before_cursor_execute", _on_execute)
            db.close()
        return count

    small, large = _count(_scenario(2)), _count(_scenario(8))
    assert small == large, f"2 people: {small} queries, 8 people: {large} - N+1 has crept in"
