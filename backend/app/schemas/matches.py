"""Schemas for mutual matches."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.discover import CandidateItem, CandidatePhoto
from app.schemas.match_contact import MatchContactOut


class MatchOut(BaseModel):
    """A current mutual match: their public card (filtered through their
    own visibility settings) plus how to reach them - the one place
    anyone's match contact info is ever returned."""
    id: UUID
    first_name: str
    photo_url: Optional[str] = None
    headline: Optional[str] = None
    photos: list[CandidatePhoto] = []
    activities: list[CandidateItem] = []
    interests: list[CandidateItem] = []
    matched_at: Optional[datetime] = None
    contact: MatchContactOut
