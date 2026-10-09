"""
Endpoints for recording a user's action toward another - see
app/models/user_interaction.py for the full design.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.user_interaction import UserInteraction
from app.schemas.interactions import InteractionOut, InteractionRequest
from app.services.email import send_email
from app.services.matches import is_mutual_match
from app.services.notifications import new_match_email
from app.services.safety import is_blocked
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/discover", tags=["discover"])


@router.post("/interact", response_model=InteractionOut, status_code=201)
def record_interaction(
    body: InteractionRequest, request: Request, background: BackgroundTasks, db: Session = Depends(get_db)
):
    user = get_current_user(request, db)

    if body.target_user_id == user.id:
        raise HTTPException(status_code=400, detail="Can't interact with yourself")

    target = db.query(User).filter(User.id == body.target_user_id).first()
    # Blocked in either direction looks exactly like a nonexistent user, so
    # the response never reveals that someone blocked you.
    if not target or is_blocked(db, user.id, target.id):
        raise HTTPException(status_code=400, detail="Invalid target_user_id")

    was_matched = is_mutual_match(db, user.id, target.id)

    existing = (
        db.query(UserInteraction)
        .filter(UserInteraction.user_id == user.id, UserInteraction.target_user_id == body.target_user_id)
        .first()
    )
    if existing:
        # Reconsidering (e.g. dismissed -> interested) updates the
        # existing row rather than violating the unique constraint with
        # a fresh insert - see model docstring.
        existing.action = body.action
        db.commit()
        db.refresh(existing)
        return _with_match_flag(db, existing, was_matched, background)

    interaction = UserInteraction(user_id=user.id, target_user_id=body.target_user_id, action=body.action)
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return _with_match_flag(db, interaction, was_matched, background)


def _with_match_flag(
    db: Session, interaction: UserInteraction, was_matched: bool, background: BackgroundTasks
) -> InteractionOut:
    """matched=True when this 'interested' completes a mutual match, so the
    Discovery page can celebrate the moment it happens. A match that's new
    with this action also emails the other person, who said Connect earlier
    and isn't looking at the screen right now."""
    matched = is_mutual_match(db, interaction.user_id, interaction.target_user_id)
    if matched and not was_matched:
        email = new_match_email(db, interaction.target_user_id, interaction.user_id)
        if email:
            background.add_task(send_email, email)
    return InteractionOut(
        id=interaction.id,
        target_user_id=interaction.target_user_id,
        action=interaction.action,
        matched=matched,
    )


@router.get("/interactions", response_model=list[InteractionOut])
def list_interactions(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return db.query(UserInteraction).filter(UserInteraction.user_id == user.id).all()
