"""
A user's pets - one-to-many (someone can have more than one dog/cat),
same pattern as user_education.py and user_language.py. See
docs/pets-design.md for the full reasoning: pets are a matching and
activity-recommendation dimension, not just a profile field.

Non-owners who are still open to dog-related activities/matches use a
separate comfortable_with_dogs flag on UserSocialProfile, not a row
here - this table is specifically for people who actually have a pet.
"""
import enum
import uuid

from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class PetType(str, enum.Enum):
    dog = "dog"
    cat = "cat"
    other = "other"


class PetSize(str, enum.Enum):
    small = "small"
    medium = "medium"
    large = "large"


class PetActivityLevel(str, enum.Enum):
    low = "low"
    moderate = "moderate"
    high = "high"


class UserPet(Base):
    __tablename__ = "user_pets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    pet_type = Column(Enum(PetType), nullable=False)
    name = Column(String, nullable=True)

    # Dog-specific fields - nullable since they don't apply to cats/other.
    size = Column(Enum(PetSize), nullable=True)
    activity_level = Column(Enum(PetActivityLevel), nullable=True)
    comfortable_with_other_dogs = Column(Boolean, nullable=True)

    visible_on_profile = Column(Boolean, nullable=False, default=False)
    usable_for_matching = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="pets")
