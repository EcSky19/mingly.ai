"""
Mutual matches. A match is never stored - it's simply two people who have
each marked the other 'interested' (see app/models/user_interaction.py),
so it can never drift out of sync with what they actually chose.
Unmatching flips your side to 'dismissed', which ends the match for both
people at once.
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import AccountStatus, User
from app.models.user_interaction import InteractionAction, UserInteraction
from app.services.safety import blocked_ids, is_blocked


def is_mutual_match(db: Session, a_id: UUID, b_id: UUID) -> bool:
    if is_blocked(db, a_id, b_id):
        return False
    count = (
        db.query(UserInteraction)
        .filter(
            UserInteraction.action == InteractionAction.interested,
            ((UserInteraction.user_id == a_id) & (UserInteraction.target_user_id == b_id))
            | ((UserInteraction.user_id == b_id) & (UserInteraction.target_user_id == a_id)),
        )
        .count()
    )
    return count == 2


def get_matches(db: Session, user_id: UUID) -> list[tuple[User, datetime | None]]:
    """Everyone the user currently has a mutual match with (active
    accounts only), newest match first. matched_at is when the second
    person said yes - the later of the two interactions."""
    mine = {
        r.target_user_id: r
        for r in db.query(UserInteraction).filter(
            UserInteraction.user_id == user_id, UserInteraction.action == InteractionAction.interested
        )
    }
    if not mine:
        return []
    theirs = (
        db.query(UserInteraction)
        .filter(
            UserInteraction.target_user_id == user_id,
            UserInteraction.action == InteractionAction.interested,
            UserInteraction.user_id.in_(list(mine.keys())),
        )
        .all()
    )
    matched_at = {}
    for r in theirs:
        times = [t for t in (r.updated_at, r.created_at, mine[r.user_id].updated_at, mine[r.user_id].created_at) if t]
        matched_at[r.user_id] = max(times) if times else None
    for other in blocked_ids(db, user_id):
        matched_at.pop(other, None)
    if not matched_at:
        return []

    users = (
        db.query(User)
        .filter(User.id.in_(list(matched_at.keys())), User.account_status == AccountStatus.active)
        .all()
    )
    result = [(u, matched_at[u.id]) for u in users]
    # (has_time, time) so a missing timestamp never gets compared against a
    # timezone-aware one (Postgres returns aware datetimes)
    result.sort(key=lambda pair: (pair[1] is not None, pair[1] or 0), reverse=True)
    return result
