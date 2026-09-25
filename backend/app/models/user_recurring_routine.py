"""
A user's recurring routines - "insert compatible people into things
you already do," per the root PRD. One-to-many, references the
existing Activity catalog (not a free-text field) so a routine stays
consistent with everything else built on that catalog, including the
"Other - type your own" submission flow for activities not yet listed.

days_of_week uses a JSON column (a plain list of strings, validated at
the API layer against a fixed 7-day vocabulary) rather than a Postgres
enum or array type - same reasoning as the social profile's multi-
select fields: JSON works natively on both Postgres and SQLite (the
test suite's engine), where Postgres's native ARRAY type does not.
"""
import enum
import uuid

from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class TimeWindow(str, enum.Enum):
    morning = "morning"
    afternoon = "afternoon"
    evening = "evening"
    late_night = "late_night"
    flexible = "flexible"


DAYS_OF_WEEK = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class UserRecurringRoutine(Base):
    __tablename__ = "user_recurring_routines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)

    days_of_week = Column(JSON, nullable=True)  # list of values from DAYS_OF_WEEK
    time_window = Column(Enum(TimeWindow), nullable=True)
    location_context = Column(String, nullable=True)  # free text, e.g. "Central Park", "my usual gym"

    is_active = Column(Boolean, nullable=False, default=True)

    visible_on_profile = Column(Boolean, nullable=False, default=False)
    usable_for_matching = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="recurring_routines")
    activity = relationship("Activity")
