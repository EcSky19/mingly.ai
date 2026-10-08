"""Schemas for blocking and reporting."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.safety import ReportReason


class BlockRequest(BaseModel):
    user_id: UUID


class BlockedPerson(BaseModel):
    """What you see about someone you blocked, in Settings - just enough to
    recognize them and unblock."""
    id: UUID
    first_name: str
    photo_url: Optional[str] = None
    blocked_at: Optional[datetime] = None


class ReportRequest(BaseModel):
    user_id: UUID
    reason: ReportReason
    details: Optional[str] = Field(default=None, max_length=2000)
    also_block: bool = True  # reporting someone usually means you don't want to see them again
