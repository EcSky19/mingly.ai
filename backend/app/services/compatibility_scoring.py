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
    intro: str = ""


@dataclass
class PairSignals:
    """What two people share, for building the friendly intro. *_named
    lists hold ONLY items the candidate left visible on their profile;
    *_total counts include hidden ones (they still count, they're just
    never named)."""
    loved_activities_named: list[str] = field(default_factory=list)
    loved_activities_total: int = 0
    liked_activities_named: list[str] = field(default_factory=list)
    liked_activities_total: int = 0
    loved_interests_named: list[str] = field(default_factory=list)
    loved_interests_total: int = 0
    liked_interests_total: int = 0
    lifestyle_matches: int = 0
    best_distance: float | None = None


# Catalog names that read awkwardly mid-sentence ("you both love golf and
# gym / weightlifting") get a natural phrasing instead. Every slash-style
# name in the live catalog is covered; anything else falls back to the
# generic lowercase rule in _casual.
CONVERSATIONAL_NAMES = {
    "Baseball / Softball": "baseball",
    "Billiards / Pool": "pool",
    "Boxing / Martial Arts": "martial arts",
    "Concerts / Live Music": "live music",
    "Coworking / Coffee Shops": "working from coffee shops",
    "Dancing / Nightclubs": "dancing",
    "Drinks / Bars": "going out for drinks",
    "Golf Simulators / Indoor Golf": "indoor golf",
    "Gym / Weightlifting": "lifting",
    "Investment / Stock Market Discussions": "talking markets",
    "Pottery / Ceramics": "pottery",
    "Sauna / Spa": "spa days",
    "Skiing / Snowboarding": "hitting the slopes",
    "Topgolf / Social Golf": "Topgolf",
    "Workout / Fitness Classes": "fitness classes",
}
MAX_NAMED_IN_INTRO = 3


def _activity_sets(rows: list[UserActivity]) -> tuple[set, set]:
    loved = {r.activity_id for r in rows if r.is_top_pick}
    liked = {r.activity_id for r in rows if not r.is_top_pick}
    return loved, liked


def _interest_sets(rows: list[UserInterest]) -> tuple[set, set]:
    loved = {r.interest_id for r in rows if r.is_top_pick}
    liked = {r.interest_id for r in rows if not r.is_top_pick}
    return loved, liked


def _describe_shared(label: str, shared_ids: set, names: dict, visible_ids: set) -> str:
    """Human-readable description of a shared-items overlap. Every
    shared item counts toward the score and the stated count (hiding
    something controls public DISPLAY, not matching), but only items
    the CANDIDATE left visible on their profile are named - naming a
    hidden one would reveal a selection they chose not to show anyone."""
    named = sorted(names.get(i, "?") for i in shared_ids if i in visible_ids)
    hidden_count = len(shared_ids) - len(named)
    text = f"{len(shared_ids)} shared {label}"
    if named:
        text += ": " + ", ".join(named)
        if hidden_count:
            text += f" (+{hidden_count} more)"
    return text


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
) -> tuple[float, list[str], PairSignals]:
    score = 0.0
    reasons: list[str] = []
    signals = PairSignals()
    visible_activity_ids = {r.activity_id for r in candidate_activities if r.visible_on_profile}
    visible_interest_ids = {r.interest_id for r in candidate_interests if r.visible_on_profile}

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
        signals.loved_activities_total = len(shared_loved_activities)
        signals.loved_activities_named = sorted(
            activity_names[a] for a in shared_loved_activities if a in visible_activity_ids and a in activity_names
        )
        reasons.append(
            _describe_shared("loved activities", shared_loved_activities, activity_names, visible_activity_ids)
        )
    if shared_liked_activities:
        score += WEIGHT_SHARED_LIKED_ACTIVITY * len(shared_liked_activities)
        signals.liked_activities_total = len(shared_liked_activities)
        signals.liked_activities_named = sorted(
            activity_names[a] for a in shared_liked_activities if a in visible_activity_ids and a in activity_names
        )
        reasons.append(f"{len(shared_liked_activities)} other shared activities")

    r_loved_int, r_liked_int = _interest_sets(requester_interests)
    c_loved_int, c_liked_int = _interest_sets(candidate_interests)
    r_all_int = r_loved_int | r_liked_int
    c_all_int = c_loved_int | c_liked_int

    shared_loved_interests = r_loved_int & c_loved_int
    shared_liked_interests = (r_all_int & c_all_int) - shared_loved_interests

    if shared_loved_interests:
        score += WEIGHT_SHARED_LOVED_INTEREST * len(shared_loved_interests)
        signals.loved_interests_total = len(shared_loved_interests)
        signals.loved_interests_named = sorted(
            interest_names[i] for i in shared_loved_interests if i in visible_interest_ids and i in interest_names
        )
        reasons.append(
            _describe_shared("loved interests", shared_loved_interests, interest_names, visible_interest_ids)
        )
    if shared_liked_interests:
        score += WEIGHT_SHARED_LIKED_INTEREST * len(shared_liked_interests)
        signals.liked_interests_total = len(shared_liked_interests)
        reasons.append(f"{len(shared_liked_interests)} other shared interests")

    # Lifestyle answers are only compared when BOTH people allowed their
    # lifestyle section to be used for matching.
    if (
        requester_social
        and candidate_social
        and requester_social.usable_for_matching
        and candidate_social.usable_for_matching
    ):
        matched_fields = [
            f
            for f in LIFESTYLE_FIELDS_TO_COMPARE
            if getattr(requester_social, f, None) and getattr(requester_social, f, None) == getattr(candidate_social, f, None)
        ]
        if matched_fields:
            score += WEIGHT_LIFESTYLE_FIELD_MATCH * len(matched_fields)
            signals.lifestyle_matches = len(matched_fields)
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
    signals.best_distance = best_distance
    if best_distance is not None:
        proximity_fraction = max(0.0, 1 - best_distance / DEFAULT_TRAVEL_RADIUS_MILES)
        score += MAX_PROXIMITY_BONUS * proximity_fraction
        if best_distance < VERY_CLOSE_MILES:
            reasons.append(f"Very close by ({best_distance:.1f} miles)")

    return score, reasons, signals


def _casual(name: str) -> str:
    """'Fitness & Wellness' -> 'fitness and wellness', keeping acronyms
    like 'AI' intact; slash-style names use their natural phrasing."""
    if name in CONVERSATIONAL_NAMES:
        return CONVERSATIONAL_NAMES[name]
    words = name.replace(" & ", " and ").split()
    return " ".join(w if (w.isupper() and len(w) > 1) else w.lower() for w in words)


def _join(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _named_phrase(named: list[str], total: int) -> str:
    shown = [_casual(n) for n in named[:MAX_NAMED_IN_INTRO]]
    if total > len(shown):
        if len(shown) == 1:
            return f"{shown[0]}, among other things"
        shown.append("more")
    return _join(shown)


def _build_intro(first_name: str, s: PairSignals) -> str:
    """A short, friend-introducing-a-friend style intro built from the
    same signals as the score. Only ever names items the candidate left
    visible; hidden overlaps are acknowledged vaguely, never named."""
    who = f"You and {first_name}" if first_name else "You two"
    sentences: list[str] = []

    if s.loved_activities_named:
        sentences.append(f"{who} both love {_named_phrase(s.loved_activities_named, s.loved_activities_total)}.")
    elif s.loved_activities_total:
        sentences.append(f"{who} love some of the same activities.")
    elif s.liked_activities_named:
        sentences.append(f"{who} both enjoy {_named_phrase(s.liked_activities_named, s.liked_activities_total)}.")
    elif s.liked_activities_total:
        sentences.append(f"{who} enjoy some of the same activities.")

    if s.loved_interests_named:
        opener = "You're also both into" if sentences else f"{who} are both into"
        sentences.append(f"{opener} {_named_phrase(s.loved_interests_named, s.loved_interests_total)}.")
    elif s.loved_interests_total or s.liked_interests_total:
        sentences.append(
            "You've got some interests in common, too." if sentences else f"{who} share some of the same interests."
        )

    if s.lifestyle_matches >= 2:
        sentences.append(
            "It sounds like you move at a similar pace, too." if sentences else f"{who} seem to move at a similar pace."
        )

    close = s.best_distance is not None and s.best_distance < VERY_CLOSE_MILES
    near = "practically neighbors" if close and s.best_distance < 1 else "close by"
    if sentences:
        if close:
            sentences.append(f"Plus, you're {near}.")
    elif close:
        sentences.append(
            f"{who} don't have much listed in common yet, but you're {near} - sometimes that's all it takes."
        )
    else:
        sentences.append(
            f"{who} don't have much listed in common yet, but you're in the same area - sometimes that's all it takes to start."
        )
    return " ".join(sentences)


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
        score, reasons, signals = _score_pair(
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
        scored.append(
            ScoredCandidate(
                user=candidate,
                score=score,
                reasons=reasons,
                intro=_build_intro((candidate.first_name or "").strip(), signals),
            )
        )

    scored.sort(key=lambda sc: sc.score, reverse=True)
    return scored
