"""
Mutual matches - see app/services/matches.py. This is the ONLY place a
person's optional match contact info is ever returned to someone else,
and only while the match is current.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user_interaction import InteractionAction, UserInteraction
from app.models.user_match_contact import UserMatchContact
from app.schemas.discover import CandidateItem, CandidatePhoto
from app.schemas.match_contact import MatchContactOut
from app.schemas.matches import MatchOut
from app.services.matches import get_matches, is_mutual_match
from app.services.public_profile import build_public_cards
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("", response_model=list[MatchOut])
def list_matches(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    matches = get_matches(db, user.id)
    if not matches:
        return []
    match_users = [m for m, _ in matches]
    cards = build_public_cards(db, match_users)
    contacts = {
        c.user_id: c
        for c in db.query(UserMatchContact).filter(UserMatchContact.user_id.in_([u.id for u in match_users])).all()
    }
    result = []
    for match_user, matched_at in matches:
        card = cards[match_user.id]
        c = contacts.get(match_user.id)
        result.append(
            MatchOut(
                id=match_user.id,
                first_name=match_user.first_name,
                photo_url=card.photo_url,
                headline=card.headline,
                photos=[CandidatePhoto(url=p.url, tag=p.tag) for p in card.photos],
                activities=[CandidateItem(name=i.name, loved=i.loved) for i in card.activities],
                interests=[CandidateItem(name=i.name, loved=i.loved) for i in card.interests],
                matched_at=matched_at,
                contact=MatchContactOut(email=c.email, phone=c.phone, instagram=c.instagram) if c else MatchContactOut(),
            )
        )
    return result


@router.delete("/{other_user_id}", status_code=204)
def unmatch(other_user_id: str, request: Request, db: Session = Depends(get_db)):
    """Ends a match for both people: flips your side to 'dismissed', so it's
    no longer mutual and your contact info stops being visible to them
    immediately. You won't be shown to each other in Discovery again."""
    user = get_current_user(request, db)
    try:
        other_uuid = uuid.UUID(other_user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Match not found")
    if not is_mutual_match(db, user.id, other_uuid):
        raise HTTPException(status_code=404, detail="Match not found")

    mine = (
        db.query(UserInteraction)
        .filter(UserInteraction.user_id == user.id, UserInteraction.target_user_id == other_uuid)
        .first()
    )
    mine.action = InteractionAction.dismissed
    db.commit()
    return Response(status_code=204)
