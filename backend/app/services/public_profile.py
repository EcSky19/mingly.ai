"""
The PUBLIC view of a person: exactly what another user is allowed to
see on a Discovery card. Every field is filtered through that person's
own visibility settings - nothing they marked not-visible-on-profile is
ever included, directly or indirectly (e.g. a photo tagged to an
activity they later hid doesn't show the tag either).

Batch-fetched for a whole candidate set in a fixed number of queries,
regardless of how many candidates there are - same N+1 discipline as
app/services/eligibility.py.
"""
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.activity import Activity, UserActivity
from app.models.interest import Interest, UserInterest
from app.models.professional_profile import ProfessionalProfile
from app.models.user import User
from app.models.user_photo import UserPhoto
from app.services.photo_storage import public_photo_url


@dataclass
class PublicItem:
    name: str
    loved: bool


@dataclass
class PublicPhoto:
    url: str
    tag: str | None = None


@dataclass
class PublicCard:
    photo_url: str | None = None
    headline: str | None = None
    photos: list[PublicPhoto] = field(default_factory=list)
    activities: list[PublicItem] = field(default_factory=list)
    interests: list[PublicItem] = field(default_factory=list)


def _headline(profile: ProfessionalProfile | None) -> str | None:
    """'Role at Company', built only from fields the person made
    visible. Professional fields default to hidden, so most people
    will have no headline until they choose to show something."""
    if profile is None:
        return None
    role = profile.current_role if profile.current_role_visible_on_profile else None
    company = profile.company if profile.company_visible_on_profile else None
    industry = profile.industry if profile.industry_visible_on_profile else None
    if role and company:
        return f"{role} at {company}"
    if role and industry:
        return f"{role} · {industry}"
    if role:
        return role
    if company:
        return f"Works at {company}"
    return industry or None


def _visible_items(rows: list, names: dict, id_attr: str) -> list[PublicItem]:
    items = [
        PublicItem(name=names[getattr(r, id_attr)], loved=r.is_top_pick)
        for r in rows
        if r.visible_on_profile and getattr(r, id_attr) in names
    ]
    # Loved first, then liked, alphabetical within each
    items.sort(key=lambda i: (not i.loved, i.name.lower()))
    return items


def build_public_cards(db: Session, users: list[User]) -> dict[UUID, PublicCard]:
    if not users:
        return {}
    ids = [u.id for u in users]

    professional = {
        p.user_id: p for p in db.query(ProfessionalProfile).filter(ProfessionalProfile.user_id.in_(ids)).all()
    }
    activity_rows = db.query(UserActivity).filter(UserActivity.user_id.in_(ids)).all()
    interest_rows = db.query(UserInterest).filter(UserInterest.user_id.in_(ids)).all()
    photo_rows = (
        db.query(UserPhoto).filter(UserPhoto.user_id.in_(ids)).order_by(UserPhoto.display_order).all()
    )

    activity_ids = {r.activity_id for r in activity_rows}
    activity_ids |= {p.tagged_activity_id for p in photo_rows if p.tagged_activity_id}
    interest_ids = {r.interest_id for r in interest_rows}
    interest_ids |= {p.tagged_interest_id for p in photo_rows if p.tagged_interest_id}

    # Always run these (an empty IN is valid) so the total query count
    # never depends on the data's shape.
    activity_names = {a.id: a.name for a in db.query(Activity).filter(Activity.id.in_(activity_ids)).all()}
    interest_names = {i.id: i.name for i in db.query(Interest).filter(Interest.id.in_(interest_ids)).all()}

    activities_by_user: dict = {}
    for r in activity_rows:
        activities_by_user.setdefault(r.user_id, []).append(r)
    interests_by_user: dict = {}
    for r in interest_rows:
        interests_by_user.setdefault(r.user_id, []).append(r)
    photos_by_user: dict = {}
    for p in photo_rows:
        photos_by_user.setdefault(p.user_id, []).append(p)

    cards = {}
    for user in users:
        user_activities = activities_by_user.get(user.id, [])
        user_interests = interests_by_user.get(user.id, [])
        visible_activity_ids = {r.activity_id for r in user_activities if r.visible_on_profile}
        visible_interest_ids = {r.interest_id for r in user_interests if r.visible_on_profile}

        photos = []
        for p in photos_by_user.get(user.id, []):
            tag = None
            if p.tagged_activity_id in visible_activity_ids:
                tag = activity_names.get(p.tagged_activity_id)
            elif p.tagged_interest_id in visible_interest_ids:
                tag = interest_names.get(p.tagged_interest_id)
            photos.append(PublicPhoto(url=f"/api/uploads/{p.file_path}", tag=tag))

        cards[user.id] = PublicCard(
            photo_url=public_photo_url(user.profile_photo_url),
            headline=_headline(professional.get(user.id)),
            photos=photos,
            activities=_visible_items(user_activities, activity_names, "activity_id"),
            interests=_visible_items(user_interests, interest_names, "interest_id"),
        )
    return cards
