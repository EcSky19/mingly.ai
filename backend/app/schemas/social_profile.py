"""
Schemas for lifestyle, career orientation, and social preferences -
the "Stage A" batch of remaining onboarding fields.
"""
from typing import Optional
from pydantic import BaseModel, field_validator

from app.models.user_social_profile import (
    CareerOrientation,
    EarlyBirdNightOwl,
    ActivityLevel,
    DrinkingPreference,
    GoingOutFrequency,
    IndoorOutdoorPreference,
    WeekdayWeekendPreference,
    SocialCadence,
    PlanningStyle,
    MeetingPreference,
    CAREER_QUALITIES,
    SOCIAL_ENVIRONMENTS,
    SOCIAL_GOALS,
)


class SocialProfileUpdate(BaseModel):
    career_orientation: Optional[CareerOrientation] = None
    career_qualities: Optional[list[str]] = None

    early_bird_night_owl: Optional[EarlyBirdNightOwl] = None
    activity_level: Optional[ActivityLevel] = None
    drinking_preference: Optional[DrinkingPreference] = None
    going_out_frequency: Optional[GoingOutFrequency] = None
    indoor_outdoor_preference: Optional[IndoorOutdoorPreference] = None
    weekday_weekend_preference: Optional[WeekdayWeekendPreference] = None

    social_cadence: Optional[SocialCadence] = None
    planning_style: Optional[PlanningStyle] = None
    meeting_preference: Optional[MeetingPreference] = None
    social_environment: Optional[list[str]] = None
    social_goals: Optional[list[str]] = None

    visible_on_profile: bool = False
    usable_for_matching: bool = True

    @field_validator("career_qualities")
    @classmethod
    def validate_career_qualities(cls, v):
        if v is None:
            return v
        invalid = set(v) - set(CAREER_QUALITIES)
        if invalid:
            raise ValueError(f"Invalid career qualities: {invalid}")
        return v

    @field_validator("social_environment")
    @classmethod
    def validate_social_environment(cls, v):
        if v is None:
            return v
        invalid = set(v) - set(SOCIAL_ENVIRONMENTS)
        if invalid:
            raise ValueError(f"Invalid social environment values: {invalid}")
        return v

    @field_validator("social_goals")
    @classmethod
    def validate_social_goals(cls, v):
        if v is None:
            return v
        invalid = set(v) - set(SOCIAL_GOALS)
        if invalid:
            raise ValueError(f"Invalid social goals: {invalid}")
        return v


class SocialProfileOut(BaseModel):
    career_orientation: Optional[CareerOrientation] = None
    career_qualities: Optional[list[str]] = None
    early_bird_night_owl: Optional[EarlyBirdNightOwl] = None
    activity_level: Optional[ActivityLevel] = None
    drinking_preference: Optional[DrinkingPreference] = None
    going_out_frequency: Optional[GoingOutFrequency] = None
    indoor_outdoor_preference: Optional[IndoorOutdoorPreference] = None
    weekday_weekend_preference: Optional[WeekdayWeekendPreference] = None
    social_cadence: Optional[SocialCadence] = None
    planning_style: Optional[PlanningStyle] = None
    meeting_preference: Optional[MeetingPreference] = None
    social_environment: Optional[list[str]] = None
    social_goals: Optional[list[str]] = None
    visible_on_profile: bool = False
    usable_for_matching: bool = True

    class Config:
        from_attributes = True
