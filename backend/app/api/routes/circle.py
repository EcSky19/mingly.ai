"""
Circles - your trusted people. Invite links create requests; accepting one
connects you both. See app/services/circles.py.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.circle import CircleConnection, CircleRequest, CircleRequestStatus
from app.models.user import AccountStatus, User
from app.schemas.circle import (
    CircleMember, CircleOut, CirclePerson, CircleRequestOut, CircleSettingsUpdate, InviteInfoOut, InviteLinkOut,
)
from app.services.circles import connect, disconnect, get_or_create_invite_code, inviter_for_code
from app.services.photo_storage import public_photo_url
from app.services.safety import is_blocked
from app.services.public_profile import build_public_cards
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/circle", tags=["circle"])
invites_router = APIRouter(prefix="/api/invites", tags=["circle"])


def _uuid_or_404(value: str, what: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail=f"{what} not found")


@router.get("", response_model=CircleOut)
def get_circle(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    connections = db.query(CircleConnection).filter(
        or_(CircleConnection.user_a_id == user.id, CircleConnection.user_b_id == user.id)
    ).all()
    connected_at = {(c.user_b_id if c.user_a_id == user.id else c.user_a_id): c.created_at for c in connections}
    pending = db.query(CircleRequest).filter(
        CircleRequest.to_user_id == user.id, CircleRequest.status == CircleRequestStatus.pending
    ).all()

    people_ids = set(connected_at) | {r.from_user_id for r in pending}
    people = {
        u.id: u
        for u in db.query(User).filter(User.id.in_(people_ids), User.account_status == AccountStatus.active).all()
    } if people_ids else {}
    cards = build_public_cards(db, list(people.values()))

    def person(uid):
        u, card = people[uid], cards[uid]
        return dict(id=u.id, first_name=u.first_name, photo_url=card.photo_url, headline=card.headline)

    members = sorted(
        (CircleMember(**person(uid), connected_at=connected_at[uid]) for uid in connected_at if uid in people),
        key=lambda m: m.first_name.lower(),
    )
    requests = [
        CircleRequestOut(id=r.id, from_user=CirclePerson(**person(r.from_user_id)), created_at=r.created_at)
        for r in pending if r.from_user_id in people
    ]
    return CircleOut(members=members, requests=requests, show_as_mutual_connection=user.show_as_mutual_connection)


@router.get("/invite-link", response_model=InviteLinkOut)
def invite_link(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    code = get_or_create_invite_code(db, user.id)
    return InviteLinkOut(code=code, url=f"{settings.APP_URL}/invite/{code}")


def _my_pending_request(db: Session, user_id, request_id: str) -> CircleRequest:
    req_uuid = _uuid_or_404(request_id, "Request")
    req = db.query(CircleRequest).filter(
        CircleRequest.id == req_uuid,
        CircleRequest.to_user_id == user_id,  # only the recipient can answer
        CircleRequest.status == CircleRequestStatus.pending,
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


@router.post("/requests/{request_id}/accept", status_code=204)
def accept_request(request_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    req = _my_pending_request(db, user.id, request_id)
    if is_blocked(db, user.id, req.from_user_id):
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = CircleRequestStatus.accepted
    connect(db, req.from_user_id, user.id, source=req.source.replace("_link", ""))
    db.commit()
    return Response(status_code=204)


@router.post("/requests/{request_id}/decline", status_code=204)
def decline_request(request_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    req = _my_pending_request(db, user.id, request_id)
    req.status = CircleRequestStatus.declined
    db.commit()
    return Response(status_code=204)


@router.delete("/members/{other_user_id}", status_code=204)
def remove_member(other_user_id: str, request: Request, db: Session = Depends(get_db)):
    """Removes someone from your circle - for both of you, since circle
    connections are always mutual."""
    user = get_current_user(request, db)
    other = _uuid_or_404(other_user_id, "Circle member")
    if not disconnect(db, user.id, other):
        raise HTTPException(status_code=404, detail="Circle member not found")
    db.commit()
    return Response(status_code=204)


@router.put("/settings", response_model=CircleSettingsUpdate)
def update_settings(body: CircleSettingsUpdate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    user.show_as_mutual_connection = body.show_as_mutual_connection
    db.commit()
    return CircleSettingsUpdate(show_as_mutual_connection=user.show_as_mutual_connection)


@invites_router.get("/{code}", response_model=InviteInfoOut)
def invite_info(code: str, db: Session = Depends(get_db)):
    inviter_id = inviter_for_code(db, code)
    inviter = db.query(User).filter(User.id == inviter_id, User.account_status == AccountStatus.active).first() if inviter_id else None
    if not inviter:
        raise HTTPException(status_code=404, detail="Invite not found")
    return InviteInfoOut(inviter_first_name=inviter.first_name, inviter_photo_url=public_photo_url(inviter.profile_photo_url))
