"""
Auth endpoints: LinkedIn login, callback, logout, current-session check, account deletion.
"""
import shutil

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.services import linkedin_auth
from app.services.session_auth import get_current_user
from app.services.photo_storage import UPLOADS_DIR

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


@router.delete("/account")
async def delete_account(request: Request, db: Session = Depends(get_db)):
    """A genuine hard delete, not a soft deactivation - AccountStatus.deleted
    exists as an enum value but isn't used here. Deleting the User row
    cascades everything else at the DB level (verified directly against
    the live schema: every users.id foreign key has ON DELETE CASCADE).
    Uploaded photo files aren't covered by that cascade since they live
    on disk, not in a table, so they're cleaned up explicitly first."""
    user = get_current_user(request, db)

    user_photo_dir = UPLOADS_DIR / str(user.id)
    if user_photo_dir.exists():
        shutil.rmtree(user_photo_dir, ignore_errors=True)

    # A bulk delete (raw SQL), not db.delete(user) - the ORM-level
    # delete tries to manage relationships itself by default, attempting
    # to SET NULL on every child row's foreign key before deleting,
    # which fails against columns that are NOT NULL (confirmed this
    # breaks against real Postgres). A bulk delete issues a plain
    # DELETE FROM users WHERE id = ... and lets the database's own
    # ON DELETE CASCADE - already verified directly against the live
    # schema - do the actual cascading work.
    db.query(User).filter(User.id == user.id).delete()
    db.commit()

    request.session.clear()
    return {"ok": True}


@router.get("/me")
async def me(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return {
        "id": str(user.id),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "onboarding_completed": user.onboarding_completed,
        "account_status": user.account_status,
        "profile_photo_url": user.profile_photo_url,
    }
