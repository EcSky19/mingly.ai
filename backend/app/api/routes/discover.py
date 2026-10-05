"""
The testable exit point for the matching engine: who is eligible to be
shown to the requesting user (app/services/eligibility.py), ranked by
compatibility score with human-readable reasons
(app/services/compatibility_scoring.py).
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user_interaction import InteractionAction, UserInteraction
from app.schemas.discover import CandidateDetail, CandidateItem, CandidateOut, CandidatePhoto
from app.services.compatibility_scoring import get_ranked_candidates
from app.services.public_profile import build_public_cards
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/discover", tags=["discover"])


@router.get("/candidates", response_model=list[CandidateOut])
def list_candidates(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    ranked = get_ranked_candidates(db, user.id)
    # People you chose "Decide later" on come after everyone you haven't seen
    # yet - still ranked by score within each group (sort is stable).
    deferred = {
        row.target_user_id
        for row in db.query(UserInteraction).filter(
            UserInteraction.user_id == user.id, UserInteraction.action == InteractionAction.later
        )
    }
    ranked = sorted(ranked, key=lambda sc: sc.user.id in deferred)
    cards = build_public_cards(db, [sc.user for sc in ranked])
    results = []
    for sc in ranked:
        card = cards[sc.user.id]
        results.append(
            CandidateOut(
                id=sc.user.id,
                first_name=sc.user.first_name,
                score=sc.score,
                reasons=sc.reasons,
                intro=sc.intro,
                deferred=sc.user.id in deferred,
                photo_url=card.photo_url,
                headline=card.headline,
                photos=[CandidatePhoto(url=p.url, tag=p.tag) for p in card.photos],
                activities=[CandidateItem(name=i.name, loved=i.loved) for i in card.activities],
                interests=[CandidateItem(name=i.name, loved=i.loved) for i in card.interests],
                details=[CandidateDetail(label=d.label, value=d.value) for d in card.details],
            )
        )
    return results
