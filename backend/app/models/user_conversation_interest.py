"""
A user's conversation interests - reuses the existing Interest catalog
(app/models/interest.py) but a separate selection, since "what I'd
enjoy talking about" is a distinct signal from "what I'm into" per
root PRD section 33, even though the underlying topic list overlaps.

Simple selected/not-selected, unlike UserInterest which also tracks
is_top_pick - conversation interests don't need a graduated intensity,
they're closer to career_qualities/social_environment in shape.
"""
import uuid

from sqlalchemy import Column, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserConversationInterest(Base):
    __tablename__ = "user_conversation_interests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    interest_id = Column(UUID(as_uuid=True), ForeignKey("interests.id", ondelete="CASCADE"), nullable=False)

    visible_on_profile = Column(Boolean, nullable=False, default=False)

    user = relationship("User", backref="conversation_interests")
    interest = relationship("Interest")
