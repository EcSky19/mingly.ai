"""
The testable exit point for hard eligibility filtering - returns who
is currently eligible to be shown to the requesting user. See
app/services/eligibility.py for the actual filtering logic.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.discover import CandidateOut
from app.services.eligibility import get_eligible_candidates
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/discover", tags=["discover"])


@router.get("/candidates", response_model=list[CandidateOut])
def list_candidates(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    candidates = get_eligible_candidates(db, user.id)
    return [CandidateOut(id=c.id, first_name=c.first_name) for c in candidates]
