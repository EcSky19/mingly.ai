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
from app.models.professional_profile import ProfessionalProfile
from app.models.user_education import UserEducation
from app.models.user_language import UserLanguage
from app.models.user_pet import UserPet
from app.models.user import AccountStatus, User
from app.models.user_location import UserLocation
from app.models.user_social_profile import UserSocialProfile
from app.services.circles import circles_for
from app.services.careers import career_family, core_role, core_role_display, family_phrase
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
# Personal info from onboarding - each only counts when BOTH people allowed
# that field to be used for matching.
WEIGHT_SHARED_LANGUAGE = 3        # English excluded: near-universal here, so no signal
# Same-college alumni is a strong signal on its own - close to a shared loved
# activity - and deliberately the same whether they graduated one year or
# twenty years apart (graduation year is intentionally not used).
WEIGHT_SAME_SCHOOL = 8
WEIGHT_SAME_FIELD_OF_STUDY = 1.5
WEIGHT_SAME_DEGREE = 1
WEIGHT_SAME_ROLE = 3              # same core role, ignoring seniority (see app/services/careers.py)
WEIGHT_SAME_CAREER_FAMILY = 2     # related roles in the same field, e.g. Data Scientist + Data Engineer
# A shared language counts fully only if both speak it at least
# conversationally; if either is still learning it, it's half the signal.
LEARNING_LANGUAGE_FACTOR = 0.5
WEIGHT_SAME_INDUSTRY = 2
WEIGHT_SAME_COMPANY = 2           # each person decides, via its toggle, whether coworkers can be matched on it
WEIGHT_SAME_CAREER_STAGE = 1.5
WEIGHT_BOTH_DOG_PEOPLE = 3
WEIGHT_DOG_FRIENDLY = 2           # one has a dog, the other is comfortable around dogs
PENALTY_DOG_MISMATCH = -3         # one has a dog, the other said they're not comfortable
WEIGHT_DOGS_NOT_SOCIAL = 1        # both have dogs, but one isn't comfortable around other dogs - dog meetups won't work
WEIGHT_SAME_DOG_ENERGY = 1        # dogs with the same activity level make easy walk/run partners
WEIGHT_SAME_DOG_SIZE = 1          # similar-size dogs play together more safely
WEIGHT_BOTH_CAT_PEOPLE = 2        # shared identity, though there's no joint outing like with dogs
WEIGHT_BOTH_PET_OWNERS = 1        # both have pets, just different kinds
WEIGHT_SHARED_SOCIAL_GOAL = 2
# Friends of friends: someone you share a circle member with is a warm
# introduction, not a stranger. Counted per mutual friend, capped.
WEIGHT_MUTUAL_FRIEND = 4
MAX_MUTUAL_FRIENDS_COUNTED = 3
MAX_MUTUAL_FRIENDS_NAMED = 2
MAX_EXTRAS_IN_INTRO = 2           # keep the intro a friendly few lines, not a wall
LIFESTYLE_PACE_MIN_MATCHES = 3

# Answers that express no preference - two people both saying "either"
# doesn't make them similar, so these never count as a lifestyle match.
NON_SIGNAL_VALUES = {"either", "flexible", "depends_on_activity", "prefer_not_to_say"}

GOAL_PHRASES = {
    "regular_friends": "new friends",
    "activity_partners": "activity partners",
    "broader_social_circle": "a broader social circle",
    "people_with_similar_lifestyles": "people with similar lifestyles",
    "professional_peers": "connections with professional peers",
}

LIFESTYLE_FIELDS_TO_COMPARE = [
    "activity_level",
    "going_out_frequency",
    "social_cadence",
    "indoor_outdoor_preference",
    "early_bird_night_owl",
    "drinking_preference",
    "weekday_weekend_preference",
    "planning_style",
    "meeting_preference",
    "spending_preference",
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
    lifestyle_matches: int = 0          # only set when the candidate's lifestyle section is visible
    best_distance: float | None = None
    languages_named: list[str] = field(default_factory=list)
    schools_named: list[str] = field(default_factory=list)
    industry_named: str | None = None
    role_named: str | None = None
    company_named: str | None = None
    career_family_named: str | None = None
    both_dog_people: bool = False
    both_cat_people: bool = False
    mutual_friends_named: list[str] = field(default_factory=list)  # only friends who allow being named
    mutual_friends_total: int = 0
    goals_named: list[str] = field(default_factory=list)


@dataclass
class PersonalInfo:
    """One person's onboarding personal info, batch-fetched for scoring."""
    social: UserSocialProfile | None = None
    professional: ProfessionalProfile | None = None
    education: list = field(default_factory=list)
    languages: list = field(default_factory=list)
    pets: list = field(default_factory=list)


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
        matched_fields = []
        for f in LIFESTYLE_FIELDS_TO_COMPARE:
            value = getattr(requester_social, f, None)
            value = getattr(value, "value", value)
            other = getattr(candidate_social, f, None)
            other = getattr(other, "value", other)
            if value and value not in NON_SIGNAL_VALUES and value == other:
                matched_fields.append(f)
        if matched_fields:
            score += WEIGHT_LIFESTYLE_FIELD_MATCH * len(matched_fields)
            # Saying "you're alike" reveals their answers, so it's only
            # mentioned when they made their lifestyle section visible.
            if candidate_social.visible_on_profile:
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


def _norm(text: str | None) -> str:
    return (text or "").strip().lower()


def _score_personal_info(r: PersonalInfo, c: PersonalInfo, signals: PairSignals) -> tuple[float, list[str]]:
    """Signals from onboarding personal info. Every one follows the same
    two consent rules:
      - it only COUNTS when both people allowed that field for matching;
      - it's only MENTIONED (reasons/intro) when the candidate made the
        underlying field visible on their profile - even 'you both work
        in tech' reveals their industry, so it's treated like naming it.
    """
    score = 0.0
    reasons: list[str] = []

    # Languages (English excluded - near-universal here, so no signal)
    r_langs = {_norm(l.language): l for l in r.languages if l.usable_for_matching and l.language}
    c_langs = {_norm(l.language): l for l in c.languages if l.usable_for_matching and l.language}
    shared = sorted(k for k in set(r_langs) & set(c_langs) if k != "english")
    if shared:
        for k in shared:
            levels = {getattr(x.proficiency, "value", x.proficiency) for x in (r_langs[k], c_langs[k])}
            factor = LEARNING_LANGUAGE_FACTOR if "learning" in levels else 1.0
            score += WEIGHT_SHARED_LANGUAGE * factor
        named = [c_langs[k].language.strip() for k in shared if c_langs[k].visible_on_profile]
        signals.languages_named = named
        if named:
            reasons.append(f"Both speak {', '.join(named)}")

    # Education: same school; same field of study
    r_edu = [e for e in r.education if e.usable_for_matching]
    c_edu = [e for e in c.education if e.usable_for_matching]
    r_schools = {_norm(e.school) for e in r_edu if e.school}
    c_schools = {_norm(e.school): e for e in c_edu if e.school}
    shared_schools = sorted(r_schools & set(c_schools))
    if shared_schools:
        score += WEIGHT_SAME_SCHOOL * len(shared_schools)
        named = [c_schools[k].school.strip() for k in shared_schools if c_schools[k].visible_on_profile]
        signals.schools_named = named
        if named:
            reasons.append(f"Both went to {', '.join(named)}")
    r_fields = {_norm(e.field_of_study) for e in r_edu if e.field_of_study}
    c_fields = {_norm(e.field_of_study): e for e in c_edu if e.field_of_study}
    shared_fields = r_fields & set(c_fields)
    if shared_fields:
        score += WEIGHT_SAME_FIELD_OF_STUDY * len(shared_fields)
        if any(c_fields[k].visible_on_profile for k in shared_fields):
            reasons.append("Studied the same field")
    r_degrees = {_norm(e.degree) for e in r_edu if e.degree}
    c_degrees = {_norm(e.degree): e for e in c_edu if e.degree}
    shared_degrees = r_degrees & set(c_degrees)
    if shared_degrees:
        score += WEIGHT_SAME_DEGREE
        if any(c_degrees[k].visible_on_profile for k in shared_degrees):
            reasons.append("Same degree")

    # Professional: same role, company, industry, career stage. Company is
    # sensitive (it can match coworkers), so like everything else it only
    # counts when BOTH people allowed it via its toggle.
    rp, cp = r.professional, c.professional
    if rp and cp:
        if (
            rp.current_role_usable_for_matching and cp.current_role_usable_for_matching
            and rp.current_role and cp.current_role
        ):
            # Similar careers, not just identical titles: same core role first,
            # otherwise the same career family.
            r_family, c_family = career_family(rp.current_role), career_family(cp.current_role)
            if core_role(rp.current_role) == core_role(cp.current_role):
                score += WEIGHT_SAME_ROLE
                if cp.current_role_visible_on_profile:
                    # The shared CORE role, true for both - not their exact title,
                    # which may include a seniority the requester doesn't have.
                    signals.role_named = core_role_display(cp.current_role)
                    reasons.append(f"Both work as {signals.role_named}")
            elif r_family and r_family == c_family:
                score += WEIGHT_SAME_CAREER_FAMILY
                if cp.current_role_visible_on_profile:
                    signals.career_family_named = family_phrase(c_family)
                    reasons.append(f"Similar careers ({family_phrase(c_family)})")
        if (
            rp.company_usable_for_matching and cp.company_usable_for_matching
            and rp.company and _norm(rp.company) == _norm(cp.company)
        ):
            score += WEIGHT_SAME_COMPANY
            if cp.company_visible_on_profile:
                signals.company_named = cp.company.strip()
                reasons.append(f"Both work at {signals.company_named}")
        if (
            rp.industry_usable_for_matching and cp.industry_usable_for_matching
            and rp.industry and _norm(rp.industry) == _norm(cp.industry)
        ):
            score += WEIGHT_SAME_INDUSTRY
            if cp.industry_visible_on_profile:
                signals.industry_named = cp.industry.strip()
                reasons.append(f"Both work in {cp.industry.strip()}")
        if (
            rp.career_stage_usable_for_matching and cp.career_stage_usable_for_matching
            and rp.career_stage and rp.career_stage == cp.career_stage
        ):
            score += WEIGHT_SAME_CAREER_STAGE
            if cp.career_stage_visible_on_profile:
                reasons.append("At a similar career stage")

    # Pets. Each pet entry has its own "usable for matching" toggle.
    def _pets(info: PersonalInfo, kind: str | None = None):
        return [
            p for p in info.pets
            if p.usable_for_matching and (kind is None or getattr(p.pet_type, "value", p.pet_type) == kind)
        ]

    def _val(x):
        return getattr(x, "value", x)

    def _comfortable(info: PersonalInfo):
        if info.social and info.social.usable_for_matching:
            return info.social.comfortable_with_dogs
        return None

    r_dogs, c_dogs = _pets(r, "dog"), _pets(c, "dog")
    r_cats, c_cats = _pets(r, "cat"), _pets(c, "cat")
    if r_dogs and c_dogs:
        # Both dog people. If either dog isn't comfortable around other dogs,
        # dog meetups won't work, so it's a much weaker signal.
        dogs_social = all(d.comfortable_with_other_dogs is not False for d in r_dogs + c_dogs)
        score += WEIGHT_BOTH_DOG_PEOPLE if dogs_social else WEIGHT_DOGS_NOT_SOCIAL
        if any(p.visible_on_profile for p in c_dogs):
            signals.both_dog_people = True
            reasons.append("Both have dogs")
        r_energy = {_val(d.activity_level) for d in r_dogs if d.activity_level}
        c_energy = {_val(d.activity_level) for d in c_dogs if d.activity_level}
        if r_energy & c_energy:
            score += WEIGHT_SAME_DOG_ENERGY
        r_size = {_val(d.size) for d in r_dogs if d.size}
        c_size = {_val(d.size) for d in c_dogs if d.size}
        if r_size & c_size:
            score += WEIGHT_SAME_DOG_SIZE
    elif r_dogs or c_dogs:
        other_comfortable = _comfortable(c) if r_dogs else _comfortable(r)
        if other_comfortable is True:
            score += WEIGHT_DOG_FRIENDLY
        elif other_comfortable is False:
            score += PENALTY_DOG_MISMATCH  # real friction; never mentioned

    if r_cats and c_cats:
        score += WEIGHT_BOTH_CAT_PEOPLE
        if any(p.visible_on_profile for p in c_cats):
            signals.both_cat_people = True
            reasons.append("Both have cats")
    elif _pets(r) and _pets(c) and not (r_dogs and c_dogs):
        # Both have pets, just not the same kind (e.g. a cat and a rabbit)
        score += WEIGHT_BOTH_PET_OWNERS

    # Shared social goals
    rs, cs = r.social, c.social
    if rs and cs and rs.usable_for_matching and cs.usable_for_matching:
        shared_goals = [g for g in (cs.social_goals or []) if g in set(rs.social_goals or [])]
        if shared_goals:
            score += WEIGHT_SHARED_SOCIAL_GOAL * len(shared_goals)
            if cs.visible_on_profile:
                signals.goals_named = [GOAL_PHRASES.get(g, g.replace("_", " ")) for g in shared_goals]
                reasons.append(f"Both looking for {', '.join(signals.goals_named)}")

    return score, reasons


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

    # Personal-info extras, most distinctive first, capped so the intro
    # stays a friendly few lines. Every one is already visibility-gated.
    extras: list[str] = []  # verb phrases: "<who> both <phrase>"
    if s.schools_named:
        extras.append(f"went to {_join(s.schools_named)}")
    if s.languages_named:
        extras.append(f"speak {_join(s.languages_named)}")
    if s.role_named:
        role = _casual(s.role_named)
        first = role.split()[0] if role.split() else ""
        article = "an" if role[:1] in "aeiou" and not (first.isupper() and len(first) > 1) else "a"
        extras.append(f"work as {article} {role}")
    if s.career_family_named and not s.role_named:
        extras.append(f"work in {s.career_family_named}")
    if s.company_named:
        extras.append(f"work at {s.company_named}")
    if s.both_dog_people:
        extras.append("are dog people")
    if s.both_cat_people:
        extras.append("are cat people")
    if s.industry_named and not (s.role_named or s.career_family_named or s.company_named):
        extras.append(f"work in {_casual(s.industry_named)}")
    if s.goals_named:
        extras.append(f"are looking for {_join(s.goals_named[:2])}")
    if extras:
        chosen = extras[:MAX_EXTRAS_IN_INTRO]
        if chosen[0].startswith("are "):
            # "You're both dog people and looking for..." rather than
            # "You both are dog people and are looking for..."
            rest = [c[len("are "):] if c.startswith("are ") else c for c in chosen]
            lead = "You're" if sentences else f"{who} are"
            sentences.append(f"{lead} both {' and '.join(rest)}.")
        else:
            subject = "You" if sentences else who
            sentences.append(f"{subject} both {' and '.join(chosen)}.")

    if s.mutual_friends_named:
        shown = s.mutual_friends_named[:MAX_MUTUAL_FRIENDS_NAMED]
        tail = ", among others" if s.mutual_friends_total > len(shown) else ""
        subject = "You" if sentences else who
        sentences.append(f"{subject} both know {_join(shown)}{tail}.")

    if s.lifestyle_matches >= LIFESTYLE_PACE_MIN_MATCHES:
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

    everyone = candidate_ids + [user_id]
    # Friends of friends: everyone's circle in one query, then the mutual
    # friends' names and naming permission in one more.
    circles = circles_for(db, everyone)
    mutual_ids = set().union(*(circles[user_id] & circles.get(c, set()) for c in candidate_ids)) if candidate_ids else set()
    mutual_people = {
        u.id: u
        for u in db.query(User).filter(User.id.in_(mutual_ids), User.account_status == AccountStatus.active).all()
    }
    info: dict = {uid: PersonalInfo() for uid in everyone}
    info[user_id].social = requester_social
    for uid, sp in social_by_user.items():
        info[uid].social = sp
    for p in db.query(ProfessionalProfile).filter(ProfessionalProfile.user_id.in_(everyone)).all():
        info[p.user_id].professional = p
    for e in db.query(UserEducation).filter(UserEducation.user_id.in_(everyone)).all():
        info[e.user_id].education.append(e)
    for l in db.query(UserLanguage).filter(UserLanguage.user_id.in_(everyone)).all():
        info[l.user_id].languages.append(l)
    for pet in db.query(UserPet).filter(UserPet.user_id.in_(everyone)).all():
        info[pet.user_id].pets.append(pet)

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
        extra_score, extra_reasons = _score_personal_info(info[user_id], info[candidate.id], signals)
        mutual = circles[user_id] & circles.get(candidate.id, set())
        mutual_active = [mutual_people[m] for m in mutual if m in mutual_people]
        if mutual_active:
            signals.mutual_friends_total = len(mutual_active)
            extra_score += WEIGHT_MUTUAL_FRIEND * min(len(mutual_active), MAX_MUTUAL_FRIENDS_COUNTED)
            # Only friends who allow it are ever named; the rest still count.
            signals.mutual_friends_named = sorted(p.first_name for p in mutual_active if p.show_as_mutual_connection)
            if signals.mutual_friends_named:
                extra_reasons.append(f"Mutual friends: {', '.join(signals.mutual_friends_named)}")
        score += extra_score
        reasons += extra_reasons
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
