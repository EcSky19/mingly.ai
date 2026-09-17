"""
Schemas for location, interests, and activities - the "Stage 1" pieces
of the rest of onboarding. See docs/roadmap.md.
"""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.models.activity import (
    ActivityCategory,
    SkillLevel,
    ActivityStyle,
    DesiredFrequency,
    InterestStrength,
    PreferredGroupSize,
)


# --- Location ---

class LocationCreate(BaseModel):
    city: Optional[str] = None
    metro: Optional[str] = None
    neighborhood: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    travel_radius_miles: Optional[int] = None
    transport_preferences: Optional[str] = None
    is_primary: bool = False
    label: Optional[str] = None


class LocationOut(BaseModel):
    id: UUID
    city: Optional[str] = None
    metro: Optional[str] = None
    neighborhood: Optional[str] = None
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


class UserActivityUpsert(BaseModel):
    activity_id: UUID
    interest_strength: Optional[InterestStrength] = None
    skill_level: Optional[SkillLevel] = None
    activity_style: Optional[ActivityStyle] = None
    desired_frequency: Optional[DesiredFrequency] = None
    preferred_group_size: Optional[PreferredGroupSize] = None
    is_top_pick: bool = False
    wants_to_do_now: bool = False
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
    skill_level: Optional[SkillLevel] = None
    activity_style: Optional[ActivityStyle] = None
    desired_frequency: Optional[DesiredFrequency] = None
    preferred_group_size: Optional[PreferredGroupSize] = None
    is_top_pick: bool
    wants_to_do_now: bool
    visible_on_profile: bool
