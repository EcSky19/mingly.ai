"""
Schemas for recurring routines - see app/models/user_recurring_routine.py.
"""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, field_validator

from app.models.user_recurring_routine import TimeWindow, DAYS_OF_WEEK


class RoutineCreate(BaseModel):
    activity_id: UUID
    days_of_week: Optional[list[str]] = None
    time_window: Optional[TimeWindow] = None
    location_context: Optional[str] = None
    is_active: bool = True
    visible_on_profile: bool = False
    usable_for_matching: bool = True

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, v):
        if v is None:
            return v
        invalid = set(v) - set(DAYS_OF_WEEK)
        if invalid:
            raise ValueError(f"Invalid days_of_week: {invalid}")
        return v


class RoutineUpdate(BaseModel):
    """Partial update - e.g. toggling is_active to pause a routine
    without deleting it, or adjusting the schedule."""
    days_of_week: Optional[list[str]] = None
    time_window: Optional[TimeWindow] = None
    location_context: Optional[str] = None
    is_active: Optional[bool] = None
    visible_on_profile: Optional[bool] = None
    usable_for_matching: Optional[bool] = None

    @field_validator("days_of_week")
    @classmethod
    def validate_days(cls, v):
        if v is None:
            return v
        invalid = set(v) - set(DAYS_OF_WEEK)
        if invalid:
            raise ValueError(f"Invalid days_of_week: {invalid}")
        return v


class RoutineOut(BaseModel):
    id: UUID
    activity_id: UUID
    activity_name: str
    days_of_week: Optional[list[str]] = None
    time_window: Optional[TimeWindow] = None
    location_context: Optional[str] = None
    is_active: bool
    visible_on_profile: bool
    usable_for_matching: bool
