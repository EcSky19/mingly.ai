"""
Lifestyle, career/life orientation, and social preferences - all
single-value-per-user fields (one row, not multi-entry like education
or languages). Privacy is one group-level pair, same reasoning as
UserInterest/UserActivity: per-field toggles for ~13 fields would be
an unreasonable amount of onboarding UI.

Multi-select fields (career_qualities, social_environment, social_goals)
use a JSON column (storing a plain list) rather than full catalog+join
tables, since each is a small, genuinely fixed list (not an open/growing
taxonomy the way Interests or Activities are) - a join table would be
over-engineering for ~6-9 fixed options. JSON was chosen over Postgres's
native ARRAY type specifically because ARRAY has no SQLite equivalent
(confirmed: SQLite's compiler has no visit_ARRAY method at all), and the
test suite runs against SQLite - JSON works natively on both.
"""
import enum
import uuid

from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class CareerOrientation(str, enum.Enum):
    career_focused_building_life_outside = "career_focused_building_life_outside"
    very_career_driven = "very_career_driven"
    entrepreneurial = "entrepreneurial"
    grad_or_professional_school = "grad_or_professional_school"
    established_expanding_social_life = "established_expanding_social_life"
    balanced = "balanced"


class EarlyBirdNightOwl(str, enum.Enum):
    early_bird = "early_bird"
    night_owl = "night_owl"
    either = "either"


class ActivityLevel(str, enum.Enum):
    active = "active"
    moderate = "moderate"
    relaxed = "relaxed"


class DrinkingPreference(str, enum.Enum):
    non_drinker = "non_drinker"
    social_drinker = "social_drinker"
    regular_drinker = "regular_drinker"
    prefer_not_to_say = "prefer_not_to_say"


class GoingOutFrequency(str, enum.Enum):
    rarely = "rarely"
    sometimes = "sometimes"
    often = "often"
    very_often = "very_often"


class IndoorOutdoorPreference(str, enum.Enum):
    indoor = "indoor"
    outdoor = "outdoor"
    either = "either"


class WeekdayWeekendPreference(str, enum.Enum):
    weekdays = "weekdays"
    weekends = "weekends"
    either = "either"


class SocialCadence(str, enum.Enum):
    multiple_times_per_week = "multiple_times_per_week"
    about_once_per_week = "about_once_per_week"
    a_few_times_per_month = "a_few_times_per_month"
    occasionally = "occasionally"


class PlanningStyle(str, enum.Enum):
    spontaneous = "spontaneous"
    a_day_or_two_ahead = "a_day_or_two_ahead"
    several_days_ahead = "several_days_ahead"
    about_a_week_ahead = "about_a_week_ahead"
    flexible = "flexible"


class MeetingPreference(str, enum.Enum):
    one_on_one = "one_on_one"
    small_groups = "small_groups"
    either = "either"
    prefer_bringing_someone_known = "prefer_bringing_someone_known"


class SpendingPreference(str, enum.Enum):
    inexpensive = "inexpensive"
    moderate = "moderate"
    occasional_splurge = "occasional_splurge"
    premium = "premium"
    depends_on_activity = "depends_on_activity"


class CityCircleStatus(str, enum.Enum):
    new_here = "new_here"
    know_some_want_to_expand = "know_some_want_to_expand"
    have_circle_want_more = "have_circle_want_more"
    mainly_activity_partners = "mainly_activity_partners"


class GenderIdentity(str, enum.Enum):
    woman = "woman"
    man = "man"
    non_binary = "non_binary"
    self_describe = "self_describe"
    prefer_not_to_say = "prefer_not_to_say"


class AgeRange(str, enum.Enum):
    """Bucketed, not exact - more privacy-conscious than collecting an
    exact birth date, and matches how the age PREFERENCE field works
    below (bucket-to-bucket, since we never have an exact age to filter
    numerically against)."""
    age_18_24 = "18_24"
    age_25_29 = "25_29"
    age_30_34 = "30_34"
    age_35_39 = "35_39"
    age_40_49 = "40_49"
    age_50_plus = "50_plus"
    prefer_not_to_say = "prefer_not_to_say"


# Valid values for the age_preference multi-select - "everyone" is
# mutually exclusive with specific buckets, same rule as mingle
# preference's "everyone" (matching that field's terminology exactly).
AGE_PREFERENCE_OPTIONS = ["18_24", "25_29", "30_34", "35_39", "40_49", "50_plus", "everyone"]


# Valid values for mingle_preference - a fixed vocabulary, not a DB
# enum, same JSON-array approach as career_qualities/social_goals.
# "everyone" is mutually exclusive with the specific groups - enforced
# in the schema validator, not just the frontend UI.
MINGLE_PREFERENCE_OPTIONS = ["women", "men", "non_binary", "everyone"]


# Valid values for the array fields - enforced at the API layer (Pydantic),
# not as a Postgres enum, since these are arrays of a fixed vocabulary
# rather than a single enum column.
CAREER_QUALITIES = [
    "ambitious", "curious", "active", "creative", "entrepreneurial",
    "intellectually_engaged", "laid_back", "adventurous",
]

SOCIAL_ENVIRONMENTS = [
    "conversation_focused", "activity_focused", "low_key", "lively", "outdoors", "anything",
]

SOCIAL_GOALS = [
    "regular_friends", "activity_partners", "broader_social_circle",
    "people_with_similar_lifestyles", "professional_peers",
]


class UserSocialProfile(Base):
    __tablename__ = "user_social_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    career_orientation = Column(Enum(CareerOrientation), nullable=True)
    career_qualities = Column(JSON, nullable=True)

    early_bird_night_owl = Column(Enum(EarlyBirdNightOwl), nullable=True)
    activity_level = Column(Enum(ActivityLevel), nullable=True)
    drinking_preference = Column(Enum(DrinkingPreference), nullable=True)
    going_out_frequency = Column(Enum(GoingOutFrequency), nullable=True)
    indoor_outdoor_preference = Column(Enum(IndoorOutdoorPreference), nullable=True)
    weekday_weekend_preference = Column(Enum(WeekdayWeekendPreference), nullable=True)

    social_cadence = Column(Enum(SocialCadence), nullable=True)
    planning_style = Column(Enum(PlanningStyle), nullable=True)
    meeting_preference = Column(Enum(MeetingPreference), nullable=True)
    social_environment = Column(JSON, nullable=True)
    social_goals = Column(JSON, nullable=True)

    # Stage B additions
    spending_preference = Column(Enum(SpendingPreference), nullable=True)
    city_circle_status = Column(Enum(CityCircleStatus), nullable=True)
    comfortable_with_dogs = Column(Boolean, nullable=True)  # for non-owners, per docs/pets-design.md

    # "About You" - gender identity gets its OWN dedicated privacy pair,
    # independent of the group-level visible_on_profile/usable_for_matching
    # above, since it's identity-sensitive and deserves control separate
    # from the broader lifestyle/social block.
    gender_identity = Column(Enum(GenderIdentity), nullable=True)
    gender_identity_description = Column(String, nullable=True)  # free text, only used when self_describe
    gender_identity_visible_on_profile = Column(Boolean, nullable=False, default=False)
    gender_identity_usable_for_matching = Column(Boolean, nullable=False, default=True)

    # Same reasoning as gender_identity - own dedicated privacy pair,
    # not the group-level flag.
    age_range = Column(Enum(AgeRange), nullable=True)
    age_range_visible_on_profile = Column(Boolean, nullable=False, default=False)
    age_range_usable_for_matching = Column(Boolean, nullable=False, default=True)

    # mingle_preference deliberately has NO privacy columns at all - this
    # is never shown to anyone, including the people it affects, by
    # design, not just by UI choice. Structurally impossible to expose
    # via the API since no such field exists to toggle.
    mingle_preference = Column(JSON, nullable=True)  # list from MINGLE_PREFERENCE_OPTIONS

    # Same "never exposed" reasoning as mingle_preference.
    age_preference = Column(JSON, nullable=True)  # list from AGE_PREFERENCE_OPTIONS

    visible_on_profile = Column(Boolean, nullable=False, default=False)
    usable_for_matching = Column(Boolean, nullable=False, default=True)

    user = relationship("User", backref="social_profile", uselist=False)
