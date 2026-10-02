"""
Structured compatibility scoring: given the list of ELIGIBLE candidates
(see app/services/eligibility.py for the binary yes/no gate that runs
first - this module never re-decides eligibility, only ranks within
it), score and rank them by how compatible they actually are.

V0 heuristic - explicit, named, tunable weight constants rather than
scattered magic numbers, so this can be adjusted without touching the
scoring logic itself. Not yet ML-driven; that's a later phase, once
there's real behavioral data worth training on.

Weights reflect the product's stated priorities:
- Shared ACTIVITIES outweigh shared INTERESTS, per the root PRD's
  activities-first thesis ("insert compatible people into things you
  already do").
- LOVED selections outweigh merely LIKED ones, but liked selections
  still count - an explicit product decision (liked items should play
  a role in matching, just a smaller one than loved items).
"""
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.activity import Activity, UserActivity
from app.models.interest import Interest, UserInterest
from app.models.user import User
from app.models.user_location import UserLocation
from app.models.user_social_profile import UserSocialProfile
from app.services.eligibility import DEFAULT_TRAVEL_RADIUS_MILES, _haversine_miles, get_eligible_candidates

WEIGHT_SHARED_LOVED_ACTIVITY = 10
WEIGHT_SHARED_LIKED_ACTIVITY = 3
WEIGHT_SHARED_LOVED_INTEREST = 5
WEIGHT_SHARED_LIKED_INTEREST = 1.5
WEIGHT_LIFESTYLE_FIELD_MATCH = 2
MAX_PROXIMITY_BONUS = 10
VERY_CLOSE_MILES = 5

# Simple exact-match lifestyle fields for V0 - fields where an equal
# value plausibly signals compatibility. Deliberately not attempting
# nuanced compatibility logic yet (e.g. early-bird/night-owl pairing
# rules) - that's a real design question for a later iteration, not
# something to guess at for V0.
LIFESTYLE_FIELDS_TO_COMPARE = [
    "activity_level",
    "going_out_frequency",
    "social_cadence",
    "indoor_outdoor_preference",
]


@dataclass
class ScoredCandidate:
    user: User
    score: float
    reasons: list[str] = field(default_factory=list)


def _activity_sets(rows: list[UserActivity]) -> tuple[set, set]:
    loved = {r.activity_id for r in rows if r.is_top_pick}
    liked = {r.activity_id for r in rows if not r.is_top_pick}
    return loved, liked


def _interest_sets(rows: list[UserInterest]) -> tuple[set, set]:
    loved = {r.interest_id for r in rows if r.is_top_pick}
    liked = {r.interest_id for r in rows if not r.is_top_pick}
    return loved, liked


def _score_pair(
    requester_activities: list[UserActivity],
    requester_interests: list[UserInterest],
    requester_social: UserSocialProfile | None,
    requester_locations: list[UserLocation],
    candidate_activities: list[UserActivity],
    candidate_interests: list[UserInterest],
    candidate_social: UserSocialProfile | None,
    candidate_locations: list[UserLocation],
    activity_names: dict,
    interest_names: dict,
) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    r_loved_act, r_liked_act = _activity_sets(requester_activities)
    c_loved_act, c_liked_act = _activity_sets(candidate_activities)
    r_all_act = r_loved_act | r_liked_act
    c_all_act = c_loved_act | c_liked_act

    shared_loved_activities = r_loved_act & c_loved_act
    # Anything shared that isn't already counted as shared-loved, so a
    # loved+loved pair never also gets counted again as "liked".
    shared_liked_activities = (r_all_act & c_all_act) - shared_loved_activities

    if shared_loved_activities:
        score += WEIGHT_SHARED_LOVED_ACTIVITY * len(shared_loved_activities)
        names = ", ".join(sorted(activity_names.get(a, "?") for a in shared_loved_activities))
        reasons.append(f"{len(shared_loved_activities)} shared loved activities: {names}")
    if shared_liked_activities:
        score += WEIGHT_SHARED_LIKED_ACTIVITY * len(shared_liked_activities)
        reasons.append(f"{len(shared_liked_activities)} other shared activities")

    r_loved_int, r_liked_int = _interest_sets(requester_interests)
    c_loved_int, c_liked_int = _interest_sets(candidate_interests)
    r_all_int = r_loved_int | r_liked_int
    c_all_int = c_loved_int | c_liked_int

    shared_loved_interests = r_loved_int & c_loved_int
    shared_liked_interests = (r_all_int & c_all_int) - shared_loved_interests

    if shared_loved_interests:
        score += WEIGHT_SHARED_LOVED_INTEREST * len(shared_loved_interests)
        names = ", ".join(sorted(interest_names.get(i, "?") for i in shared_loved_interests))
        reasons.append(f"{len(shared_loved_interests)} shared loved interests: {names}")
    if shared_liked_interests:
        score += WEIGHT_SHARED_LIKED_INTEREST * len(shared_liked_interests)
        reasons.append(f"{len(shared_liked_interests)} other shared interests")

    if requester_social and candidate_social:
        matched_fields = [
            f
            for f in LIFESTYLE_FIELDS_TO_COMPARE
            if getattr(requester_social, f, None) and getattr(requester_social, f, None) == getattr(candidate_social, f, None)
        ]
        if matched_fields:
            score += WEIGHT_LIFESTYLE_FIELD_MATCH * len(matched_fields)
            reasons.append(f"Similar lifestyle ({len(matched_fields)} shared preferences)")

    best_distance = None
    for r_loc in requester_locations:
        if r_loc.latitude is None or r_loc.longitude is None:
            continue
        for c_loc in candidate_locations:
            if c_loc.latitude is None or c_loc.longitude is None:
                continue
            d = _haversine_miles(r_loc.latitude, r_loc.longitude, c_loc.latitude, c_loc.longitude)
            if best_distance is None or d < best_distance:
                best_distance = d
    if best_distance is not None:
        proximity_fraction = max(0.0, 1 - best_distance / DEFAULT_TRAVEL_RADIUS_MILES)
        score += MAX_PROXIMITY_BONUS * proximity_fraction
        if best_distance < VERY_CLOSE_MILES:
            reasons.append(f"Very close by ({best_distance:.1f} miles)")

    return score, reasons


def get_ranked_candidates(db: Session, user_id: UUID) -> list[ScoredCandidate]:
    """The real exit point for Week 3's compatibility scoring stage:
    eligible candidates (from get_eligible_candidates), scored and
    sorted highest-first, each with a human-readable list of reasons -
    the 'explainable' part of the original matching-engine spec."""
    eligible = get_eligible_candidates(db, user_id)
    if not eligible:
        return []

    requester_activities = db.query(UserActivity).filter(UserActivity.user_id == user_id).all()
    requester_interests = db.query(UserInterest).filter(UserInterest.user_id == user_id).all()
    requester_social = db.query(UserSocialProfile).filter(UserSocialProfile.user_id == user_id).first()
    requester_locations = db.query(UserLocation).filter(UserLocation.user_id == user_id).all()

    candidate_ids = [c.id for c in eligible]

    activities_by_user: dict = {}
    all_activity_ids = set()
    for row in db.query(UserActivity).filter(UserActivity.user_id.in_(candidate_ids)).all():
        activities_by_user.setdefault(row.user_id, []).append(row)
        all_activity_ids.add(row.activity_id)
    all_activity_ids.update(a.activity_id for a in requester_activities)

    interests_by_user: dict = {}
    all_interest_ids = set()
    for row in db.query(UserInterest).filter(UserInterest.user_id.in_(candidate_ids)).all():
        interests_by_user.setdefault(row.user_id, []).append(row)
        all_interest_ids.add(row.interest_id)
    all_interest_ids.update(i.interest_id for i in requester_interests)

    social_by_user = {
        sp.user_id: sp
        for sp in db.query(UserSocialProfile).filter(UserSocialProfile.user_id.in_(candidate_ids)).all()
    }
    locations_by_user: dict = {}
    for loc in db.query(UserLocation).filter(UserLocation.user_id.in_(candidate_ids)).all():
        locations_by_user.setdefault(loc.user_id, []).append(loc)

    activity_names = {
        a.id: a.name for a in db.query(Activity).filter(Activity.id.in_(all_activity_ids)).all()
    }
    interest_names = {
        i.id: i.name for i in db.query(Interest).filter(Interest.id.in_(all_interest_ids)).all()
    }

    scored = []
    for candidate in eligible:
        score, reasons = _score_pair(
            requester_activities,
            requester_interests,
            requester_social,
            requester_locations,
            activities_by_user.get(candidate.id, []),
            interests_by_user.get(candidate.id, []),
            social_by_user.get(candidate.id),
            locations_by_user.get(candidate.id, []),
            activity_names,
            interest_names,
        )
        scored.append(ScoredCandidate(user=candidate, score=score, reasons=reasons))

    scored.sort(key=lambda sc: sc.score, reverse=True)
    return scored
