"""Schemas for Circles."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CirclePerson(BaseModel):
    """What you see about someone in your circle (or someone asking to
    join it) - their public card, filtered through their own visibility
    settings like everywhere else."""
    id: UUID
    first_name: str
    photo_url: Optional[str] = None
    headline: Optional[str] = None


class CircleMember(CirclePerson):
    connected_at: Optional[datetime] = None


class CircleRequestOut(BaseModel):
    id: UUID
    from_user: CirclePerson
    created_at: Optional[datetime] = None


class CircleOut(BaseModel):
    members: list[CircleMember]
    requests: list[CircleRequestOut]
    show_as_mutual_connection: bool


class InviteLinkOut(BaseModel):
    code: str
    url: str


class CircleSettingsUpdate(BaseModel):
    show_as_mutual_connection: bool


class InviteInfoOut(BaseModel):
    """Public, for the invite landing page: only the inviter's first name
    and photo - just enough to recognize who's inviting you."""
    inviter_first_name: str
    inviter_photo_url: Optional[str] = None
