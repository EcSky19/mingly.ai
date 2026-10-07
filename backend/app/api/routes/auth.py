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
from app.services.circles import INVITE_CODE_RE, inviter_for_code, request_from_invite
from app.services.session_auth import get_current_user
from app.services.photo_storage import UPLOADS_DIR, LINKEDIN_PHOTOS_DIR, public_photo_url, save_linkedin_photo

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/linkedin/login")
async def linkedin_login(request: Request, invite: str | None = None):
    redirect_url, state = linkedin_auth.build_authorization_url()
    request.session["oauth_state"] = state
    # An invite link sends people here with ?invite=CODE. Keep it in the
    # session so it survives the round trip to LinkedIn and back.
    if invite and INVITE_CODE_RE.match(invite):
        request.session["invite_code"] = invite
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
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Re-downloaded on every login, not just at account creation: LinkedIn's
    # picture claim is a signed URL that expires after about a week
    # (confirmed against real stored URLs), so storing it directly means
    # every user's photo silently breaks around a week after signup. We
    # keep our own permanent copy instead - see save_linkedin_photo's
    # docstring. Doing this on every login (not just once) also means a
    # profile picture change on LinkedIn is picked up here next time they
    # sign back in, rather than freezing at whatever it was at signup.
    linkedin_picture_url = userinfo.get("picture")
    if linkedin_picture_url:
        saved_path = await save_linkedin_photo(str(user.id), linkedin_picture_url)
        if saved_path:
            user.profile_photo_url = saved_path
            db.commit()

    request.session["user_id"] = str(user.id)

    # Signed in through someone's invite link: ask this person to confirm
    # adding the inviter to their circle (works for new and existing users).
    inviter_id = inviter_for_code(db, request.session.pop("invite_code", None))
    if inviter_id:
        request_from_invite(db, inviter_id, user.id)

    destination = f"{settings.APP_URL}/onboarding" if not user.onboarding_completed else f"{settings.APP_URL}/home"
    return RedirectResponse(destination)


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.post("/onboarding-complete")
async def complete_onboarding(request: Request, db: Session = Depends(get_db)):
    """Marks onboarding finished - called when someone leaves the last
    onboarding page (Finish or Skip; every path through onboarding
    converges there). Idempotent.

    Before this endpoint existed, nothing ever set the flag: it was read
    by the eligibility filter (which requires it) and the login redirect,
    but never written - so every real user was excluded from matching
    and every returning login was sent back into onboarding."""
    user = get_current_user(request, db)
    if not user.onboarding_completed:
        user.onboarding_completed = True
        db.commit()
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

    linkedin_photo_file = LINKEDIN_PHOTOS_DIR / f"{user.id}.jpg"
    linkedin_photo_file.unlink(missing_ok=True)

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
        # Stored as a relative path to our own saved copy (or, for rows
        # not yet refreshed by a login, LinkedIn's legacy full URL) -
        # public_photo_url handles both shapes.
        "profile_photo_url": public_photo_url(user.profile_photo_url),
    }
