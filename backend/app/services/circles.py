"""
Circle logic shared by the circle routes, the LinkedIn sign-in flow (invite
links), and matching (friends-of-friends). See app/models/circle.py.
"""
import re
import secrets
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.circle import CircleConnection, CircleRequest, CircleRequestStatus, UserInviteCode

INVITE_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{6,32}$")


def _pair(a: UUID, b: UUID) -> tuple[UUID, UUID]:
    """Canonical order for a connection row (matches the database check
    constraint user_a_id < user_b_id - Postgres and Python order UUIDs the
    same way, by their 128-bit value)."""
    return (a, b) if a < b else (b, a)


def circle_ids(db: Session, user_id: UUID) -> set[UUID]:
    rows = db.query(CircleConnection).filter(
        or_(CircleConnection.user_a_id == user_id, CircleConnection.user_b_id == user_id)
    )
    return {r.user_b_id if r.user_a_id == user_id else r.user_a_id for r in rows}


def circles_for(db: Session, user_ids: list[UUID]) -> dict[UUID, set[UUID]]:
    """Batch version of circle_ids: everyone's circle in one query."""
    ids = set(user_ids)
    result: dict[UUID, set[UUID]] = {uid: set() for uid in ids}
    if not ids:
        return result
    rows = db.query(CircleConnection).filter(
        or_(CircleConnection.user_a_id.in_(ids), CircleConnection.user_b_id.in_(ids))
    )
    for r in rows:
        if r.user_a_id in result:
            result[r.user_a_id].add(r.user_b_id)
        if r.user_b_id in result:
            result[r.user_b_id].add(r.user_a_id)
    return result


def are_connected(db: Session, a: UUID, b: UUID) -> bool:
    low, high = _pair(a, b)
    return (
        db.query(CircleConnection)
        .filter(CircleConnection.user_a_id == low, CircleConnection.user_b_id == high)
        .first()
        is not None
    )


def connect(db: Session, a: UUID, b: UUID, source: str = "invite") -> None:
    """Idempotent: connecting two people who are already connected is a no-op."""
    if a == b or are_connected(db, a, b):
        return
    low, high = _pair(a, b)
    db.add(CircleConnection(user_a_id=low, user_b_id=high, source=source))


def disconnect(db: Session, a: UUID, b: UUID) -> bool:
    low, high = _pair(a, b)
    deleted = (
        db.query(CircleConnection)
        .filter(CircleConnection.user_a_id == low, CircleConnection.user_b_id == high)
        .delete()
    )
    return deleted > 0


def get_or_create_invite_code(db: Session, user_id: UUID) -> str:
    row = db.query(UserInviteCode).filter(UserInviteCode.user_id == user_id).first()
    if row:
        return row.code
    while True:
        code = secrets.token_urlsafe(6)  # 8 URL-safe characters
        if not db.query(UserInviteCode).filter(UserInviteCode.code == code).first():
            break
    db.add(UserInviteCode(user_id=user_id, code=code))
    db.commit()
    return code


def inviter_for_code(db: Session, code: str | None) -> UUID | None:
    if not code or not INVITE_CODE_RE.match(code):
        return None
    row = db.query(UserInviteCode).filter(UserInviteCode.code == code).first()
    return row.user_id if row else None


def request_from_invite(db: Session, inviter_id: UUID, invitee_id: UUID) -> None:
    """Someone signed in through an invite link: ask them to confirm adding
    the inviter to their circle. The inviter already consented by sharing
    their link; the invitee confirms by accepting. Skips yourself and people
    you're already connected to; reopens a request you'd declined, since
    opening the link again is a new signal of intent."""
    from app.services.safety import is_blocked  # local import: safety imports this module

    if inviter_id == invitee_id or are_connected(db, inviter_id, invitee_id) or is_blocked(db, inviter_id, invitee_id):
        return
    existing = (
        db.query(CircleRequest)
        .filter(CircleRequest.from_user_id == inviter_id, CircleRequest.to_user_id == invitee_id)
        .first()
    )
    if existing:
        if existing.status == CircleRequestStatus.declined:
            existing.status = CircleRequestStatus.pending
    else:
        db.add(CircleRequest(from_user_id=inviter_id, to_user_id=invitee_id, source="invite_link"))
    db.commit()
