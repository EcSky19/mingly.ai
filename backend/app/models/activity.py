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
    nightlife = "nightlife"


class DesiredFrequency(str, enum.Enum):
    rarely = "rarely"
    monthly = "monthly"
    weekly = "weekly"
    multiple_times_per_week = "multiple_times_per_week"


class InterestStrength(str, enum.Enum):
    """How much a user wants to do this activity - per root PRD section 20."""
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


class ActivitySubtag(Base):
    """A finer-grained option under a specific activity - e.g. "NFL"
    under "Football Watch Parties," or "Fly Fishing" under "Fishing."
    Exists to preserve richer matching signal without bloating the main
    activity selector with hundreds of narrow entries (see root PRD's
    "do not interrogate users about every minor activity").

    Honest scope: only seeded for a handful of activities where subtags
    add real value (see app/data/activity_subtags_starter.json), not
    every one of the 111 catalog activities."""
    __tablename__ = "activity_subtags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)

    activity = relationship("Activity", backref="subtags")


class UserActivitySubtag(Base):
    """A user's chosen subtag(s) for one of their selected activities.
    Many-to-many between a user's activity selection and the subtag
    catalog - a user can pick more than one (e.g. both "NFL" and
    "College Football")."""
    __tablename__ = "user_activity_subtags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_activity_id = Column(UUID(as_uuid=True), ForeignKey("user_activities.id", ondelete="CASCADE"), nullable=False, index=True)
    subtag_id = Column(UUID(as_uuid=True), ForeignKey("activity_subtags.id", ondelete="CASCADE"), nullable=False)

    subtag = relationship("ActivitySubtag")


class UserActivity(Base):
    """A user's selected activity plus context. Top 3 activities get
    significant ranking weight per root PRD section 20 - is_top_pick
    flags those. Same group-level privacy pattern as UserInterest."""
    __tablename__ = "user_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)

    interest_strength = Column(Enum(InterestStrength), nullable=True)
    desired_frequency = Column(Enum(DesiredFrequency), nullable=True)
    preferred_group_size = Column(Enum(PreferredGroupSize), nullable=True)

    is_top_pick = Column(Boolean, nullable=False, default=False)  # top 3 this month, per root PRD
    target_timeframe = Column(Enum(TargetTimeframe), nullable=True)

    visible_on_profile = Column(Boolean, nullable=False, default=True)

    user = relationship("User", backref="activities")
    activity = relationship("Activity")
    chosen_subtags = relationship("UserActivitySubtag", backref="user_activity", cascade="all, delete-orphan")
