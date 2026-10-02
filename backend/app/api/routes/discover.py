"""
The testable exit point for the matching engine: who is eligible to be
shown to the requesting user (app/services/eligibility.py), ranked by
compatibility score with human-readable reasons
(app/services/compatibility_scoring.py).
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.discover import CandidateOut
from app.services.compatibility_scoring import get_ranked_candidates
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/discover", tags=["discover"])


@router.get("/candidates", response_model=list[CandidateOut])
def list_candidates(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    ranked = get_ranked_candidates(db, user.id)
    return [
        CandidateOut(id=sc.user.id, first_name=sc.user.first_name, score=sc.score, reasons=sc.reasons)
        for sc in ranked
    ]
