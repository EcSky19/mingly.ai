"""
Endpoints for setting a user's conversation interests - reuses the
existing Interests catalog (see app/models/user_conversation_interest.py
for why this is a separate selection from regular Interests).
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.interest import Interest
from app.models.user_conversation_interest import UserConversationInterest
from app.schemas.discovery_profile import ConversationInterestOut, ConversationInterestSet
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/profile/conversation-interests", tags=["conversation-interests"])


@router.get("", response_model=list[ConversationInterestOut])
def get_conversation_interests(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    rows = db.query(UserConversationInterest).filter(UserConversationInterest.user_id == user.id).all()
    return [
        ConversationInterestOut(
            interest_id=r.interest_id, name=r.interest.name, visible_on_profile=r.visible_on_profile
        )
        for r in rows
    ]


@router.put("", response_model=list[ConversationInterestOut])
def set_conversation_interests(
    body: ConversationInterestSet, request: Request, db: Session = Depends(get_db)
):
    """Replaces the user's full conversation-interest selection in one
    call, same pattern as PUT /api/profile/interests."""
    user = get_current_user(request, db)

    valid_ids = {
        row.id for row in db.query(Interest.id).filter(Interest.id.in_(body.interest_ids)).all()
    }
    if valid_ids != set(body.interest_ids):
        raise HTTPException(status_code=400, detail="One or more interest_ids are not valid")

    db.query(UserConversationInterest).filter(UserConversationInterest.user_id == user.id).delete()

    for interest_id in body.interest_ids:
        db.add(
            UserConversationInterest(
                user_id=user.id,
                interest_id=interest_id,
                visible_on_profile=body.visible_on_profile,
            )
        )
    db.commit()

    rows = db.query(UserConversationInterest).filter(UserConversationInterest.user_id == user.id).all()
    return [
        ConversationInterestOut(
            interest_id=r.interest_id, name=r.interest.name, visible_on_profile=r.visible_on_profile
        )
        for r in rows
    ]
