"""
Blocking and reporting. Enforcement lives in app/services/safety.py; these
routes only let people create and manage their own blocks and reports.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.safety import UserBlock, UserReport
from app.models.user import User
from app.schemas.safety import BlockedPerson, BlockRequest, ReportRequest
from app.services.photo_storage import public_photo_url
from app.services.safety import block, unblock
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api", tags=["safety"])


def _existing_other_user(db: Session, me: User, other_id) -> User:
    if other_id == me.id:
        raise HTTPException(status_code=400, detail="You can't do that to yourself")
    other = db.query(User).filter(User.id == other_id).first()
    if not other:
        raise HTTPException(status_code=404, detail="User not found")
    return other


@router.post("/blocks", status_code=204)
def block_user(body: BlockRequest, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    other = _existing_other_user(db, user, body.user_id)
    block(db, user.id, other.id)
    return Response(status_code=204)


@router.get("/blocks", response_model=list[BlockedPerson])
def list_blocks(request: Request, db: Session = Depends(get_db)):
    """Only the people YOU blocked - never who blocked you."""
    user = get_current_user(request, db)
    rows = (
        db.query(UserBlock, User)
        .join(User, User.id == UserBlock.blocked_id)
        .filter(UserBlock.blocker_id == user.id)
        .order_by(User.first_name)
        .all()
    )
    return [
        BlockedPerson(id=u.id, first_name=u.first_name, photo_url=public_photo_url(u.profile_photo_url), blocked_at=b.created_at)
        for b, u in rows
    ]


@router.delete("/blocks/{other_user_id}", status_code=204)
def unblock_user(other_user_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    try:
        other_uuid = uuid.UUID(other_user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Block not found")
    if not unblock(db, user.id, other_uuid):
        raise HTTPException(status_code=404, detail="Block not found")
    return Response(status_code=204)


@router.post("/reports", status_code=201)
def report_user(body: ReportRequest, request: Request, db: Session = Depends(get_db)):
    """Reports go to the Mingly team for review. The reported person is never
    told who reported them."""
    user = get_current_user(request, db)
    other = _existing_other_user(db, user, body.user_id)
    details = (body.details or "").strip() or None
    db.add(UserReport(reporter_id=user.id, reported_id=other.id, reason=body.reason, details=details))
    db.commit()
    if body.also_block:
        block(db, user.id, other.id)
    return {"ok": True}
