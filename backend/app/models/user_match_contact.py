"""
How someone's MATCHES can reach them - entirely optional. Kept in its own
table, separate from every other profile field, because it's the most
sensitive thing a person can share here: it's only ever returned to its
owner and to their current mutual matches (both marked each other
interested), never on a Discovery card, never to anyone else. Unmatching
immediately ends that visibility.
"""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.session import Base


class UserMatchContact(Base):
    __tablename__ = "user_match_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    instagram = Column(String, nullable=True)  # stored without the leading @

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
