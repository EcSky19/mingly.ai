"""
Blocking, enforced centrally. A block in either direction separates two
people everywhere: Discover, matches (including contact info), circles,
circle requests, and friend-of-friend introductions. Every surface asks
this module, so no feature - and no future ranking model - can reintroduce
a blocked person.
"""
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.circle import CircleRequest
from app.models.safety import UserBlock
from app.models.user_interaction import InteractionAction, UserInteraction
from app.services.circles import disconnect


def blocked_ids(db: Session, user_id: UUID) -> set[UUID]:
    """Everyone separated from this user by a block, in either direction."""
    rows = db.query(UserBlock).filter(or_(UserBlock.blocker_id == user_id, UserBlock.blocked_id == user_id))
    return {r.blocked_id if r.blocker_id == user_id else r.blocker_id for r in rows}


def is_blocked(db: Session, a: UUID, b: UUID) -> bool:
    return (
        db.query(UserBlock)
        .filter(or_(
            and_(UserBlock.blocker_id == a, UserBlock.blocked_id == b),
            and_(UserBlock.blocker_id == b, UserBlock.blocked_id == a),
        ))
        .first()
        is not None
    )


def block(db: Session, blocker_id: UUID, blocked_id: UUID) -> None:
    """Idempotent. Besides the block itself:
    - removes any circle connection and pending circle requests between them;
    - records a pass from the blocker, so unblocking later never silently
      resurrects a match or puts them back in each other's feeds."""
    if blocker_id == blocked_id:
        raise ValueError("cannot block yourself")
    if not db.query(UserBlock).filter(UserBlock.blocker_id == blocker_id, UserBlock.blocked_id == blocked_id).first():
        db.add(UserBlock(blocker_id=blocker_id, blocked_id=blocked_id))

    disconnect(db, blocker_id, blocked_id)
    db.query(CircleRequest).filter(or_(
        and_(CircleRequest.from_user_id == blocker_id, CircleRequest.to_user_id == blocked_id),
        and_(CircleRequest.from_user_id == blocked_id, CircleRequest.to_user_id == blocker_id),
    )).delete(synchronize_session=False)

    mine = (
        db.query(UserInteraction)
        .filter(UserInteraction.user_id == blocker_id, UserInteraction.target_user_id == blocked_id)
        .first()
    )
    if mine:
        mine.action = InteractionAction.dismissed
    else:
        db.add(UserInteraction(user_id=blocker_id, target_user_id=blocked_id, action=InteractionAction.dismissed))
    db.commit()


def unblock(db: Session, blocker_id: UUID, blocked_id: UUID) -> bool:
    """Only the person who blocked can unblock. The pass recorded when
    blocking stays, so nothing is resurrected automatically."""
    deleted = (
        db.query(UserBlock)
        .filter(UserBlock.blocker_id == blocker_id, UserBlock.blocked_id == blocked_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted > 0
