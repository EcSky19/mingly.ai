"""
Who can message whom, decided live on every request (never stored):

  - a current mutual match, or a circle connection,
  - both accounts active,
  - and no block in either direction.

Friends of friends can't message directly - they match first - so nobody
receives unsolicited messages. Losing the relationship (unmatch, leaving a
circle, a block) closes the conversation at once for both people; its
history stays hidden unless they reconnect.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.messaging import Conversation, Message
from app.models.user import AccountStatus, User
from app.services.circles import are_connected, circle_ids
from app.services.matches import get_matches, is_mutual_match
from app.services.safety import blocked_ids, is_blocked

MAX_MESSAGE_LENGTH = 2000
RATE_LIMIT_MESSAGES = 30  # per sender, per RATE_LIMIT_WINDOW
RATE_LIMIT_WINDOW = timedelta(minutes=1)


def now() -> datetime:
    return datetime.now(timezone.utc)


def _pair(a: UUID, b: UUID) -> tuple[UUID, UUID]:
    return (a, b) if str(a) < str(b) else (b, a)


def relationship(db: Session, user_id: UUID, other_id: UUID) -> str | None:
    """'circle', 'match', or None if these two can't message right now."""
    if user_id == other_id or is_blocked(db, user_id, other_id):
        return None
    other = db.query(User).filter(User.id == other_id).first()
    if not other or other.account_status != AccountStatus.active:
        return None
    if are_connected(db, user_id, other_id):
        return "circle"
    if is_mutual_match(db, user_id, other_id):
        return "match"
    return None


def relationships(db: Session, user_id: UUID) -> dict[UUID, str]:
    """Everyone this person can message right now -> 'circle' or 'match'.
    One batch of queries, for the conversation list."""
    allowed = {u.id: "match" for u, _ in get_matches(db, user_id)}  # already excludes blocked + inactive
    circle = circle_ids(db, user_id) - blocked_ids(db, user_id)
    if circle:
        active = {
            uid for (uid,) in db.query(User.id).filter(User.id.in_(circle), User.account_status == AccountStatus.active)
        }
        allowed.update({uid: "circle" for uid in active})
    return allowed


def find_conversation(db: Session, a: UUID, b: UUID) -> Conversation | None:
    low, high = _pair(a, b)
    return db.query(Conversation).filter(Conversation.user_a_id == low, Conversation.user_b_id == high).first()


def get_or_create_conversation(db: Session, a: UUID, b: UUID) -> Conversation:
    conversation = find_conversation(db, a, b)
    if conversation:
        return conversation
    low, high = _pair(a, b)
    conversation = Conversation(user_a_id=low, user_b_id=high)
    db.add(conversation)
    db.flush()
    return conversation


def other_id(conversation: Conversation, user_id: UUID) -> UUID:
    return conversation.user_b_id if conversation.user_a_id == user_id else conversation.user_a_id


def mark_read(conversation: Conversation, user_id: UUID) -> None:
    if conversation.user_a_id == user_id:
        conversation.user_a_read_at = now()
    else:
        conversation.user_b_read_at = now()


def _read_at(conversation: Conversation, user_id: UUID):
    return conversation.user_a_read_at if conversation.user_a_id == user_id else conversation.user_b_read_at


def unread_counts(db: Session, user_id: UUID, conversations: list[Conversation]) -> dict[UUID, int]:
    """Messages from the other person newer than when you last opened the
    conversation, per conversation."""
    counts: dict[UUID, int] = {}
    for c in conversations:  # small per person; one cheap indexed count each
        q = db.query(func.count(Message.id)).filter(Message.conversation_id == c.id, Message.sender_id != user_id)
        read_at = _read_at(c, user_id)
        if read_at is not None:
            q = q.filter(Message.created_at > read_at)
        counts[c.id] = q.scalar() or 0
    return counts


def my_conversations(db: Session, user_id: UUID) -> list[Conversation]:
    """Conversations with at least one message, newest first (unfiltered -
    callers drop the ones that are currently closed)."""
    return (
        db.query(Conversation)
        .filter(or_(Conversation.user_a_id == user_id, Conversation.user_b_id == user_id))
        .filter(Conversation.last_message_at.isnot(None))
        .order_by(Conversation.last_message_at.desc())
        .all()
    )


def sending_too_fast(db: Session, sender_id: UUID) -> bool:
    recent = (
        db.query(func.count(Message.id))
        .filter(Message.sender_id == sender_id, Message.created_at > now() - RATE_LIMIT_WINDOW)
        .scalar()
    )
    return (recent or 0) >= RATE_LIMIT_MESSAGES
