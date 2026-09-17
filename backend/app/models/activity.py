"""
Activities: distinct from interests (see root PRD section 20 - "an
interest means I enjoy this; an activity means I would actually do this
with another person"). Catalog table plus a rich join table capturing
per-activity context, since activity compatibility is a major
recommendation feature (root PRD section 40).
"""
import enum
import uuid

from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class ActivityCategory(str, enum.Enum):
    sports = "sports"
    social_food = "social_food"
    entertainment = "entertainment"
    outdoor = "outdoor"
    casual = "casual"
    pets = "pets"


class SkillLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    competitive = "competitive"
    not_applicable = "not_applicable"


class ActivityStyle(str, enum.Enum):
    casual_social = "casual_social"
    fitness_focused = "fitness_focused"
    competitive = "competitive"
    exploratory = "exploratory"  # e.g. "trying new restaurants" vs "regulars"


class DesiredFrequency(str, enum.Enum):
    rarely = "rarely"
    monthly = "monthly"
    weekly = "weekly"
    multiple_times_per_week = "multiple_times_per_week"


class InterestStrength(str, enum.Enum):
    """How much a user wants to do this activity, distinct from how
    skilled they are at it (see SkillLevel) - per root PRD section 20."""
    casual = "casual"
    moderate = "moderate"
    high = "high"


class TargetTimeframe(str, enum.Enum):
    """When a user wants to do one of their top-pick activities. Replaced
    a simple wants_to_do_now boolean after feedback that a single yes/no
    loses real information - a top pick for skiing genuinely means
    "this winter," while a top pick for coffee might mean "this week."
    Friendly wording matches the product's overall voice."""
    ready_now = "ready_now"  # "Ready now" - this week
    sometime_soon = "sometime_soon"  # "Sometime soon" - this month
    when_season_right = "when_season_right"  # "When the season's right" - this season
    no_rush = "no_rush"  # "No rush, just excited" - flexible, still a real top pick


class PreferredGroupSize(str, enum.Enum):
    one_on_one = "one_on_one"
    small_group = "small_group"
    either = "either"


class Activity(Base):
    """Catalog of selectable activities. Seeded via migration - see
    app/data/activities_starter.json."""
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True, index=True)
    category = Column(Enum(ActivityCategory), nullable=False)


class UserActivity(Base):
    """A user's selected activity plus context. Top 3 activities get
    significant ranking weight per root PRD section 20 - is_top_pick
    flags those. Same group-level privacy pattern as UserInterest."""
    __tablename__ = "user_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)

    interest_strength = Column(Enum(InterestStrength), nullable=True)
    skill_level = Column(Enum(SkillLevel), nullable=True)
    activity_style = Column(Enum(ActivityStyle), nullable=True)
    desired_frequency = Column(Enum(DesiredFrequency), nullable=True)
    preferred_group_size = Column(Enum(PreferredGroupSize), nullable=True)

    is_top_pick = Column(Boolean, nullable=False, default=False)  # top 3 this month, per root PRD
    target_timeframe = Column(Enum(TargetTimeframe), nullable=True)

    visible_on_profile = Column(Boolean, nullable=False, default=True)

    user = relationship("User", backref="activities")
    activity = relationship("Activity")
