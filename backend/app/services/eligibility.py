"""
Hard eligibility filtering: who is even eligible to be shown to whom,
before any compatibility scoring happens. This is a binary yes/no gate,
not a ranked/scored thing - scoring is a later stage.

Filters applied, in order:
1. Candidate account is active
2. Candidate has completed onboarding
3. Not the requesting user themselves
4. Neither person has already interacted with the other (either
   direction, any action) - once a decision has been made, that person
   should never resurface as a "new" candidate. See
   app/models/user_interaction.py.
5. Bidirectional gender/mingle_preference compatibility
6. Bidirectional age_range/age_preference compatibility
7. Real distance math: at least one pair of (requester location,
   candidate location) must be within BOTH people's stated travel
   radius - respects both people's own stated willingness to travel,
   not just one side's.
"""
import math
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_interaction import UserInteraction
from app.models.user_location import UserLocation
from app.models.user_social_profile import UserSocialProfile

DEFAULT_TRAVEL_RADIUS_MILES = 25  # used only if a location has no radius set
EARTH_RADIUS_MILES = 3958.8

# gender_identity values don't literally match mingle_preference's bucket
# vocabulary (singular "woman" vs plural "women" bucket), so they need an
# explicit mapping. self_describe and prefer_not_to_say are deliberately
# left unmapped: we can't know which bucket (if any) fits a self-described
# identity, and guessing risks mischaracterizing someone. Unmapped
# genders are only ever reachable through an "everyone" preference, never
# through someone narrowing to specific buckets.
GENDER_TO_MINGLE_BUCKET = {
    "woman": "women",
    "man": "men",
    "non_binary": "non_binary",
}

# age_range values already match age_preference's bucket vocabulary
# directly, except prefer_not_to_say, which - same reasoning as above -
# is only reachable through "everyone", not a specific-bucket preference.
AGE_RANGE_TO_PREFERENCE_BUCKET = {
    "18_24": "18_24",
    "25_29": "25_29",
    "30_34": "30_34",
    "35_39": "35_39",
    "40_49": "40_49",
    "50_plus": "50_plus",
}


def _preference_accepts(preference: list[str] | None, other_value: str | None, bucket_map: dict) -> bool:
    """Shared logic for both gender and age compatibility: does this
    person's stated preference accept the other person's value?"""
    if not preference or "everyone" in preference:
        return True
    if not other_value:
        return False  # unset data is only reachable via "everyone"
    bucket = bucket_map.get(other_value)
    if bucket is None:
        return False  # unmapped values (self_describe, prefer_not_to_say) - "everyone" only
    return bucket in preference


def _genders_compatible(a: UserSocialProfile | None, b: UserSocialProfile | None) -> bool:
    a_pref = a.mingle_preference if a else None
    a_gender = a.gender_identity if a else None
    b_pref = b.mingle_preference if b else None
    b_gender = b.gender_identity if b else None
    return _preference_accepts(a_pref, b_gender, GENDER_TO_MINGLE_BUCKET) and _preference_accepts(
        b_pref, a_gender, GENDER_TO_MINGLE_BUCKET
    )


def _ages_compatible(a: UserSocialProfile | None, b: UserSocialProfile | None) -> bool:
    a_pref = a.age_preference if a else None
    a_age = a.age_range if a else None
    b_pref = b.age_preference if b else None
    b_age = b.age_range if b else None
    return _preference_accepts(a_pref, b_age, AGE_RANGE_TO_PREFERENCE_BUCKET) and _preference_accepts(
        b_pref, a_age, AGE_RANGE_TO_PREFERENCE_BUCKET
    )


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


def _within_travel_radius(a_locations: list[UserLocation], b_locations: list[UserLocation]) -> bool:
    """True if ANY pair of locations puts them within BOTH people's
    stated travel radius - respects both sides' own stated willingness,
    not just one person's."""
    for a_loc in a_locations:
        if a_loc.latitude is None or a_loc.longitude is None:
            continue
        for b_loc in b_locations:
            if b_loc.latitude is None or b_loc.longitude is None:
                continue
            distance = _haversine_miles(a_loc.latitude, a_loc.longitude, b_loc.latitude, b_loc.longitude)
            a_radius = a_loc.travel_radius_miles or DEFAULT_TRAVEL_RADIUS_MILES
            b_radius = b_loc.travel_radius_miles or DEFAULT_TRAVEL_RADIUS_MILES
            if distance <= min(a_radius, b_radius):
                return True
    return False


def get_eligible_candidates(db: Session, user_id: UUID) -> list[User]:
    requester = db.query(User).filter(User.id == user_id).first()
    if not requester:
        return []

    already_interacted = set()
    for row in db.query(UserInteraction).filter(
        or_(UserInteraction.user_id == user_id, UserInteraction.target_user_id == user_id)
    ):
        already_interacted.add(row.user_id)
        already_interacted.add(row.target_user_id)
    already_interacted.discard(user_id)

    requester_social = db.query(UserSocialProfile).filter(UserSocialProfile.user_id == user_id).first()
    requester_locations = db.query(UserLocation).filter(UserLocation.user_id == user_id).all()

    candidates = (
        db.query(User)
        .filter(
            User.id != user_id,
            User.account_status == "active",
            User.onboarding_completed == True,  # noqa: E712
            ~User.id.in_(already_interacted) if already_interacted else True,
        )
        .all()
    )

    eligible = []
    for candidate in candidates:
        candidate_social = db.query(UserSocialProfile).filter(UserSocialProfile.user_id == candidate.id).first()
        if not _genders_compatible(requester_social, candidate_social):
            continue
        if not _ages_compatible(requester_social, candidate_social):
            continue
        candidate_locations = db.query(UserLocation).filter(UserLocation.user_id == candidate.id).all()
        if not _within_travel_radius(requester_locations, candidate_locations):
            continue
        eligible.append(candidate)

    return eligible
