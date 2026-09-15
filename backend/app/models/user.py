"""
Core identity model. Everything else (professional profile, interests,
activities, etc.) hangs off this via user_id foreign keys, added in
later weeks as onboarding is built out.
"""
import enum
import uuid

from sqlalchemy import Column, String, DateTime, Enum, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.session import Base


class AccountStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    banned = "banned"
    deleted = "deleted"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # LinkedIn OIDC "sub" claim - stable unique identifier for the LinkedIn account
    linkedin_sub = Column(String, unique=True, nullable=False, index=True)

    email = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    birth_year = Column(Integer, nullable=True)
    profile_photo_url = Column(String, nullable=True)

    account_status = Column(Enum(AccountStatus), nullable=False, default=AccountStatus.active)
    onboarding_completed = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True), nullable=True)
