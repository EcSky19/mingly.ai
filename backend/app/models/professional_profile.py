"""
Professional context, captured during onboarding. Every field here is
optional per docs/professional-profile-design.md - none of this is
required to complete onboarding.

Each field has a matching pair of privacy flags: whether it's shown on
the user's public profile, and whether it's usable by the recommendation
pipeline. These are independent - a user can share something for matching
purposes only, without ever displaying it publicly.
"""
import enum
import uuid

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class CareerStage(str, enum.Enum):
    student = "student"
    early_career = "early_career"
    mid_career = "mid_career"
    senior = "senior"
    founder = "founder"
    graduate_student = "graduate_student"
    career_transition = "career_transition"
    other = "other"


class ProfessionalProfile(Base):
    __tablename__ = "professional_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # --- Role ---
    current_role = Column(String, nullable=True)
    current_role_visible_on_profile = Column(Boolean, nullable=False, default=False)
    current_role_usable_for_matching = Column(Boolean, nullable=False, default=True)

    # --- Company / Industry ---
    # A user can share `company` (specific employer) OR just `industry` as a
    # lower-disclosure substitute - see docs/professional-profile-design.md.
    # company_shared tracks which path the user chose, independent of
    # whether the fields end up empty for other reasons.
    company = Column(String, nullable=True)
    company_visible_on_profile = Column(Boolean, nullable=False, default=False)
    company_usable_for_matching = Column(Boolean, nullable=False, default=True)

    industry = Column(String, nullable=True)
    industry_visible_on_profile = Column(Boolean, nullable=False, default=False)
    industry_usable_for_matching = Column(Boolean, nullable=False, default=True)

    # --- Career stage ---
    career_stage = Column(Enum(CareerStage), nullable=True)
    career_stage_visible_on_profile = Column(Boolean, nullable=False, default=False)
    career_stage_usable_for_matching = Column(Boolean, nullable=False, default=True)

    # --- Education ---
    school = Column(String, nullable=True)
    school_visible_on_profile = Column(Boolean, nullable=False, default=False)
    school_usable_for_matching = Column(Boolean, nullable=False, default=True)

    degree = Column(String, nullable=True)
    degree_visible_on_profile = Column(Boolean, nullable=False, default=False)
    degree_usable_for_matching = Column(Boolean, nullable=False, default=True)

    field_of_study = Column(String, nullable=True)
    field_of_study_visible_on_profile = Column(Boolean, nullable=False, default=False)
    field_of_study_usable_for_matching = Column(Boolean, nullable=False, default=True)

    graduation_year = Column(Integer, nullable=True)
    graduation_year_visible_on_profile = Column(Boolean, nullable=False, default=False)
    graduation_year_usable_for_matching = Column(Boolean, nullable=False, default=True)

    user = relationship("User", backref="professional_profile", uselist=False)
