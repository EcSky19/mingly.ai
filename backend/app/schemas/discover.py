"""Schemas for the discovery/candidates endpoint."""
from uuid import UUID
from pydantic import BaseModel


class CandidateOut(BaseModel):
    id: UUID
    first_name: str
