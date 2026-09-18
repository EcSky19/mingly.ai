"""
A user's spoken languages - one-to-many (someone can speak several),
same pattern as user_education.py. See root PRD section 30.
"""
import enum
import uuid

from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class LanguageProficiency(str, enum.Enum):
    native = "native"
    fluent = "fluent"
    conversational = "conversational"
    learning = "learning"


class UserLanguage(Base):
    __tablename__ = "user_languages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    language = Column(String, nullable=False)  # free text, populated via autocomplete against a bundled ISO 639-1 list
    proficiency = Column(Enum(LanguageProficiency), nullable=True)

    visible_on_profile = Column(Boolean, nullable=False, default=False)
    usable_for_matching = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="languages")
