"""
Messaging: private one-to-one conversations, so people can talk without
handing out a phone number or Instagram.

Who can message whom is decided live, every time, by app/services/messaging.py
(a current mutual match or a circle connection, and no block either way) -
it's never stored. So unmatching, leaving a circle, or blocking closes a
conversation immediately, and a later rematch reopens the same one.

One row per pair in canonical order (user_a_id < user_b_id), like circles.
Each side's "read up to" time lives on the conversation, so unread counts
need no per-message bookkeeping.
"""
import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.session import Base


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("user_a_id", "user_b_id", name="uq_conversations_pair"),
        CheckConstraint("user_a_id < user_b_id", name="ck_conversations_canonical_order"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_a_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_b_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_a_read_at = Column(DateTime(timezone=True), nullable=True)
    user_b_read_at = Column(DateTime(timezone=True), nullable=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_conversation_created", "conversation_id", "created_at"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
