"""
Pydantic schemas for the professional profile onboarding step.
"""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.models.professional_profile import CareerStage


class FieldWithPrivacy(BaseModel):
    """A value plus its two independent privacy flags. Used for every
    field in the professional profile - see docs/professional-profile-design.md."""
    value: Optional[str] = None
    visible_on_profile: bool = False
    usable_for_matching: bool = True


class ProfessionalProfileUpdate(BaseModel):
    """Request body for creating/updating a professional profile. Every
    field is optional - a user can submit a partial update, or nothing
    at all, and still complete onboarding. Education moved to a separate
    one-to-many endpoint (see EducationEntry below) since someone can
    have more than one school/degree."""
    current_role: Optional[FieldWithPrivacy] = None
    company: Optional[FieldWithPrivacy] = None
    industry: Optional[FieldWithPrivacy] = None
    career_stage: Optional[CareerStage] = None
    career_stage_visible_on_profile: bool = False
    career_stage_usable_for_matching: bool = True


class ProfessionalProfileOut(BaseModel):
    current_role: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    career_stage: Optional[CareerStage] = None

    class Config:
        from_attributes = True


class EducationEntryCreate(BaseModel):
    school: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = None
    visible_on_profile: bool = False
    usable_for_matching: bool = True


class EducationEntryOut(BaseModel):
    id: UUID
    school: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = None
    visible_on_profile: bool
    usable_for_matching: bool

    class Config:
        from_attributes = True


class LanguageEntryCreate(BaseModel):
    language: str
    proficiency: Optional[str] = None
    visible_on_profile: bool = False
    usable_for_matching: bool = True


class LanguageEntryOut(BaseModel):
    id: UUID
    language: str
    proficiency: Optional[str] = None
    visible_on_profile: bool
    usable_for_matching: bool

    class Config:
        from_attributes = True


class AutocompleteSuggestion(BaseModel):
    value: str
    subtitle: Optional[str] = None  # e.g. domain for companies, country for schools
    latitude: Optional[float] = None  # for city/neighborhood results
    longitude: Optional[float] = None


class PetCreate(BaseModel):
    pet_type: str
    name: Optional[str] = None
    size: Optional[str] = None
    activity_level: Optional[str] = None
    comfortable_with_other_dogs: Optional[bool] = None
    visible_on_profile: bool = False
    usable_for_matching: bool = True


class PetOut(BaseModel):
    id: UUID
    pet_type: str
    name: Optional[str] = None
    size: Optional[str] = None
    activity_level: Optional[str] = None
    comfortable_with_other_dogs: Optional[bool] = None
    visible_on_profile: bool
    usable_for_matching: bool

    class Config:
        from_attributes = True
