"""
Endpoints for saving/reading the professional profile onboarding step.
Requires an authenticated session (see app/api/routes/auth.py).
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.professional_profile import ProfessionalProfile
from app.schemas.professional_profile import ProfessionalProfileOut, ProfessionalProfileUpdate
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/profile/professional", tags=["professional-profile"])


@router.get("", response_model=ProfessionalProfileOut)
def get_professional_profile(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    profile = db.query(ProfessionalProfile).filter(ProfessionalProfile.user_id == user.id).first()
    if not profile:
        # No profile yet - every field optional, so an empty profile is valid.
        return ProfessionalProfileOut()
    return profile


@router.put("", response_model=ProfessionalProfileOut)
def update_professional_profile(
    body: ProfessionalProfileUpdate, request: Request, db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    profile = db.query(ProfessionalProfile).filter(ProfessionalProfile.user_id == user.id).first()
    if not profile:
        profile = ProfessionalProfile(user_id=user.id)
        db.add(profile)

    if body.current_role is not None:
        profile.current_role = body.current_role.value
        profile.current_role_visible_on_profile = body.current_role.visible_on_profile
        profile.current_role_usable_for_matching = body.current_role.usable_for_matching

    if body.company is not None:
        profile.company = body.company.value
        profile.company_visible_on_profile = body.company.visible_on_profile
        profile.company_usable_for_matching = body.company.usable_for_matching

    if body.industry is not None:
        profile.industry = body.industry.value
        profile.industry_visible_on_profile = body.industry.visible_on_profile
        profile.industry_usable_for_matching = body.industry.usable_for_matching

    if body.career_stage is not None:
        profile.career_stage = body.career_stage
        profile.career_stage_visible_on_profile = body.career_stage_visible_on_profile
        profile.career_stage_usable_for_matching = body.career_stage_usable_for_matching

    if body.school is not None:
        profile.school = body.school.value
        profile.school_visible_on_profile = body.school.visible_on_profile
        profile.school_usable_for_matching = body.school.usable_for_matching

    if body.degree is not None:
        profile.degree = body.degree.value
        profile.degree_visible_on_profile = body.degree.visible_on_profile
        profile.degree_usable_for_matching = body.degree.usable_for_matching

    if body.field_of_study is not None:
        profile.field_of_study = body.field_of_study.value
        profile.field_of_study_visible_on_profile = body.field_of_study.visible_on_profile
        profile.field_of_study_usable_for_matching = body.field_of_study.usable_for_matching

    if body.graduation_year is not None:
        profile.graduation_year = body.graduation_year
        profile.graduation_year_visible_on_profile = body.graduation_year_visible_on_profile
        profile.graduation_year_usable_for_matching = body.graduation_year_usable_for_matching

    db.commit()
    db.refresh(profile)
    return profile
