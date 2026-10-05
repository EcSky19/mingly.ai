"""Schemas for the discovery/candidates endpoint."""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CandidatePhoto(BaseModel):
    url: str
    tag: Optional[str] = None


class CandidateItem(BaseModel):
    name: str
    loved: bool


class CandidateOut(BaseModel):
    """Everything here comes from app/services/public_profile.py, which
    filters every field through the candidate's own visibility settings."""
    id: UUID
    first_name: str
    score: float
    reasons: list[str]
    intro: str = ""
    deferred: bool = False  # you chose 'Decide later' on them
    photo_url: Optional[str] = None
    headline: Optional[str] = None
    photos: list[CandidatePhoto] = []
    activities: list[CandidateItem] = []
    interests: list[CandidateItem] = []
