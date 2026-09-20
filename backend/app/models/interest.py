"""
Interests: a seeded catalog table (see app/data/interests_starter.json),
plus a join table recording which interests each user picked, with
priority (top 3-5, per root PRD section 19) and a single group-level
privacy toggle rather than per-item privacy - see docstring on
UserInterest for why.
"""
import uuid

from sqlalchemy import Column, String, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class Interest(Base):
    """Catalog of selectable interests. Seeded via migration, not
    user-editable - see app/data/interests_starter.json for the source
    list and its honestly-scoped status.

    is_user_submitted flags entries created through the "Other - type
    your own" flow rather than the seeded catalog, so they can be
    reviewed/cleaned up/promoted later rather than trusted blindly."""
    __tablename__ = "interests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True, index=True)
    is_user_submitted = Column(Boolean, nullable=False, default=False)


class UserInterest(Base):
    """A user's selected interest. Privacy is one toggle per SECTION
    (see the professional_profile pattern for per-field privacy) rather
    than per-interest - with up to 15 selected interests, per-item
    toggles would be an unreasonable amount of UI. The visible_on_profile
    flag is stored per-row for schema flexibility, but the frontend
    presents it as a single "show my interests" toggle that sets every
    row at once."""
    __tablename__ = "user_interests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    interest_id = Column(UUID(as_uuid=True), ForeignKey("interests.id", ondelete="CASCADE"), nullable=False)

    is_top_pick = Column(Boolean, nullable=False, default=False)  # top 3-5, per root PRD
    priority_rank = Column(Integer, nullable=True)  # optional ordering among top picks

    visible_on_profile = Column(Boolean, nullable=False, default=True)

    user = relationship("User", backref="interests")
    interest = relationship("Interest")
