"""
Records one user's action toward another - the foundation hard
eligibility filtering needs: once a user has acted on someone at all
(either direction), that person should never resurface as a "new"
candidate in discovery.

One row per (user_id, target_user_id) pair, not a growing history -
enforced by a unique constraint. If someone reconsiders (e.g. dismissed
then later interested, however that flow ends up working), the
existing row updates in place rather than accumulating duplicates.

A mutual match is intentionally NOT stored as its own state here - it's
just both directions having action="interested", computed by whatever
queries need it. Storing "matched" as a separate flag would let it
drift out of sync with the underlying interested rows; computing it
can't.
"""
import enum
import uuid

from sqlalchemy import Column, ForeignKey, Enum, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class InteractionAction(str, enum.Enum):
    dismissed = "dismissed"
    interested = "interested"


class UserInteraction(Base):
    __tablename__ = "user_interactions"
    __table_args__ = (UniqueConstraint("user_id", "target_user_id", name="uq_user_interaction_pair"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    action = Column(Enum(InteractionAction), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
