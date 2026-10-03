"""
Schemas for location, interests, and activities - the "Stage 1" pieces
of the rest of onboarding. See docs/roadmap.md.
"""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, field_validator

from app.models.activity import (
    ActivityCategory,
    DesiredFrequency,
    InterestStrength,
)


# --- Location ---

class LocationCreate(BaseModel):
    city: Optional[str] = None
    metro: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    travel_radius_miles: Optional[int] = None
    transport_preferences: Optional[str] = None
    is_primary: bool = False
    label: Optional[str] = None


class LocationUpdate(BaseModel):
    """Partial update of an existing location: omitted fields are left
    unchanged. is_primary can be omitted but not set to null (the column
    is NOT NULL) - an explicit null is rejected with a 422 rather than
    reaching the database."""
    city: Optional[str] = None
    metro: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    travel_radius_miles: Optional[int] = None
    transport_preferences: Optional[str] = None
    is_primary: Optional[bool] = None
    label: Optional[str] = None

    @field_validator("is_primary")
    @classmethod
    def _not_null(cls, v):
        if v is None:
            raise ValueError("may be omitted, but not set to null")
        return v


class LocationOut(BaseModel):
    id: UUID
    city: Optional[str] = None
    metro: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    travel_radius_miles: Optional[int] = None
    transport_preferences: Optional[str] = None
    is_primary: bool
    label: Optional[str] = None

    class Config:
        from_attributes = True


# --- Interests ---

class InterestCatalogOut(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class InterestSubmit(BaseModel):
    """Body for user-submitted custom interests - see
    app/models/interest.py's is_user_submitted docstring."""
    name: str


class UserInterestSet(BaseModel):
    """Request body for setting a user's full interest selection at
    once - simpler than incremental add/remove for a multi-select UI."""
    interest_ids: list[UUID]
    top_pick_ids: list[UUID] = []  # subset of interest_ids, max ~5 enforced by route
    visible_on_profile: bool = True


class UserInterestOut(BaseModel):
    interest_id: UUID
    name: str
    is_top_pick: bool
    visible_on_profile: bool


# --- Activities ---

class ActivityCatalogOut(BaseModel):
    id: UUID
    name: str
    category: ActivityCategory

    class Config:
        from_attributes = True


class ActivitySubmit(BaseModel):
    """Body for user-submitted custom activities - see
    app/models/activity.py's is_user_submitted docstring."""
    name: str


class UserActivityUpsert(BaseModel):
    activity_id: UUID
    interest_strength: Optional[InterestStrength] = None
    desired_frequency: Optional[DesiredFrequency] = None
    is_top_pick: bool = False
    visible_on_profile: bool = True


class UserActivitySet(BaseModel):
    """Same all-at-once pattern as interests, but each activity carries
    its own context rather than just being a flat id list."""
    activities: list[UserActivityUpsert]


class UserActivityOut(BaseModel):
    activity_id: UUID
    name: str
    category: ActivityCategory
    interest_strength: Optional[InterestStrength] = None
    desired_frequency: Optional[DesiredFrequency] = None
    is_top_pick: bool
    visible_on_profile: bool
