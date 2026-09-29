"""
Endpoints for recording a user's action toward another - see
app/models/user_interaction.py for the full design.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.user_interaction import UserInteraction
from app.schemas.interactions import InteractionOut, InteractionRequest
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/discover", tags=["discover"])


@router.post("/interact", response_model=InteractionOut, status_code=201)
def record_interaction(body: InteractionRequest, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)

    if body.target_user_id == user.id:
        raise HTTPException(status_code=400, detail="Can't interact with yourself")

    target = db.query(User).filter(User.id == body.target_user_id).first()
    if not target:
        raise HTTPException(status_code=400, detail="Invalid target_user_id")

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
        return existing

    interaction = UserInteraction(user_id=user.id, target_user_id=body.target_user_id, action=body.action)
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


@router.get("/interactions", response_model=list[InteractionOut])
def list_interactions(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return db.query(UserInteraction).filter(UserInteraction.user_id == user.id).all()
