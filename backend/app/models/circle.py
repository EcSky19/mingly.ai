"""
Circles: the people someone trusts. A circle connection is always mutual -
one person asked (by invite link today; by "add to circle" from a match
later) and the other accepted - so both have agreed.

Your circle's own circles form your secondary network: someone you share a
circle member with is a warm introduction ("You both know Maya") rather than
a stranger. People already in your circle never appear in Discovery - you
already know them.
"""
import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.session import Base


class CircleConnection(Base):
    """One row per connected pair, stored in a canonical order
    (user_a_id < user_b_id) so each pair can only exist once."""
    __tablename__ = "circle_connections"
    __table_args__ = (UniqueConstraint("user_a_id", "user_b_id", name="uq_circle_connections_pair"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_a_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_b_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String, nullable=False, default="invite")  # how they connected: invite (later: met)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CircleRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class CircleRequest(Base):
    """A request to join someone's circle, accepted or declined by its
    recipient. Invite links create these today; 'add a match to your
    circle' will reuse the same flow later."""
    __tablename__ = "circle_requests"
    __table_args__ = (UniqueConstraint("from_user_id", "to_user_id", name="uq_circle_requests_pair"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(CircleRequestStatus), nullable=False, default=CircleRequestStatus.pending)
    source = Column(String, nullable=False, default="invite_link")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserInviteCode(Base):
    """Each person's personal invite link code - one per person, created
    the first time they ask for their link."""
    __tablename__ = "user_invite_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    code = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
