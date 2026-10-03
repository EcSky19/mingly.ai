"""
Endpoints for lifestyle, career orientation, and social preferences.
Single row per user - same GET/PUT pattern as professional_profile.py.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user_social_profile import UserSocialProfile
from app.schemas.social_profile import SocialProfileOut, SocialProfileUpdate
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/profile/social", tags=["social-profile"])


@router.get("", response_model=SocialProfileOut)
def get_social_profile(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    profile = db.query(UserSocialProfile).filter(UserSocialProfile.user_id == user.id).first()
    if not profile:
        return SocialProfileOut()
    return profile


@router.put("", response_model=SocialProfileOut)
def update_social_profile(
    body: SocialProfileUpdate, request: Request, db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    profile = db.query(UserSocialProfile).filter(UserSocialProfile.user_id == user.id).first()
    if not profile:
        profile = UserSocialProfile(user_id=user.id)
        db.add(profile)

    # Partial update: only fields actually present in the request are
    # written. Previously every field was written, so a caller that only
    # owned some fields (the onboarding page saves lifestyle fields only)
    # silently reset everything else - including About You settings, where
    # a wiped mingle preference reads as "everyone". Sending an explicit
    # null still clears a field; omitting it leaves it untouched.
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile
