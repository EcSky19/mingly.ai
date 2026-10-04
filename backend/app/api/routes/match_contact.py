"""
Endpoints for managing your OWN optional contact info for matches. This
route only ever reads/writes the requesting user's row - showing it to a
match happens solely in the matches endpoint, and only for current
mutual matches.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user_match_contact import UserMatchContact
from app.schemas.match_contact import MatchContactOut, MatchContactUpdate
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/profile/match-contact", tags=["match-contact"])


@router.get("", response_model=MatchContactOut)
def get_match_contact(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    row = db.query(UserMatchContact).filter(UserMatchContact.user_id == user.id).first()
    if not row:
        return MatchContactOut()
    return MatchContactOut(email=row.email, phone=row.phone, instagram=row.instagram)


@router.put("", response_model=MatchContactOut)
def update_match_contact(body: MatchContactUpdate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    row = db.query(UserMatchContact).filter(UserMatchContact.user_id == user.id).first()
    if not row:
        row = UserMatchContact(user_id=user.id)
        db.add(row)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return MatchContactOut(email=row.email, phone=row.phone, instagram=row.instagram)
