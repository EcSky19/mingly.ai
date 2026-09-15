"""
Auth endpoints: LinkedIn login, callback, logout, current-session check.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services import linkedin_auth

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/linkedin/login")
async def linkedin_login(request: Request):
    redirect_url, state = linkedin_auth.build_authorization_url()
    request.session["oauth_state"] = state
    return RedirectResponse(redirect_url)


@router.get("/linkedin/callback")
async def linkedin_callback(request: Request, code: str, state: str, db: Session = Depends(get_db)):
    expected_state = request.session.pop("oauth_state", None)
    if not expected_state or expected_state != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state - possible CSRF attempt")

    access_token = await linkedin_auth.exchange_code_for_token(code)
    userinfo = await linkedin_auth.fetch_userinfo(access_token)

    linkedin_sub = userinfo["sub"]
    email = userinfo.get("email")

    user = db.query(User).filter(User.linkedin_sub == linkedin_sub).first()
    if user is None:
        # Prevent duplicate accounts: same email, different LinkedIn login attempt
        existing_by_email = db.query(User).filter(User.email == email).first() if email else None
        if existing_by_email:
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists under a different LinkedIn login.",
            )
        user = User(
            linkedin_sub=linkedin_sub,
            email=email,
            first_name=userinfo.get("given_name", ""),
            last_name=userinfo.get("family_name", ""),
            profile_photo_url=userinfo.get("picture"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    request.session["user_id"] = str(user.id)

    destination = f"{settings.APP_URL}/onboarding" if not user.onboarding_completed else f"{settings.APP_URL}/home"
    return RedirectResponse(destination)


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me")
async def me(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": str(user.id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "onboarding_completed": user.onboarding_completed,
        "account_status": user.account_status,
    }
