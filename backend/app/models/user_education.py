"""
A user's education history - one row per school/degree, since someone
can have multiple (undergrad + grad school, a bootcamp plus a degree,
etc). This replaced flat single-entry columns on professional_profiles
after early feedback made clear one entry wasn't enough - see migration
0003 and docs/professional-profile-design.md.

Privacy is one pair of flags per entry (not per-field within an entry,
unlike professional_profiles) - splitting further would be more privacy
granularity than is useful for a UX where someone is adding "a degree,"
not individually deciding whether to show their graduation year but not
their school.
"""
import uuid

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class UserEducation(Base):
    __tablename__ = "user_education"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    school = Column(String, nullable=True)
    degree = Column(String, nullable=True)
    field_of_study = Column(String, nullable=True)
    graduation_year = Column(Integer, nullable=True)

    visible_on_profile = Column(Boolean, nullable=False, default=False)
    usable_for_matching = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="education_entries")
