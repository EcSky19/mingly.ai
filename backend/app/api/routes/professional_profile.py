"""
Endpoints for saving/reading the professional profile onboarding step.
Requires an authenticated session (see app/api/routes/auth.py).

Education is handled separately - see app/api/routes/education.py -
since a user can have multiple entries (undergrad + grad school, etc).
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

    # Omitted field = leave it alone; explicit null = clear it. Clearing
    # matters: the page shares EITHER company or industry, and switching
    # must remove the other one, or it silently stays stored and keeps
    # being used for matching. Same for career stage -> "prefer not to say".
    fields_set = body.model_fields_set
    for name in ("current_role", "company", "industry"):
        if name not in fields_set:
            continue
        field = getattr(body, name)
        if field is None:
            setattr(profile, name, None)
        else:
            setattr(profile, name, field.value)
            setattr(profile, f"{name}_visible_on_profile", field.visible_on_profile)
            setattr(profile, f"{name}_usable_for_matching", field.usable_for_matching)

    if "career_stage" in fields_set:
        profile.career_stage = body.career_stage
    for toggle in ("career_stage_visible_on_profile", "career_stage_usable_for_matching"):
        if toggle in fields_set:
            setattr(profile, toggle, getattr(body, toggle))

    db.commit()
    db.refresh(profile)
    return profile
