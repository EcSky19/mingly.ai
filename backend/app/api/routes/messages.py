"""
Messaging endpoints - see app/services/messaging.py for who can message whom.

Someone you can't message (no match or circle connection, blocked in either
direction, a suspended account, or nobody at all) always gets the same 404,
so these endpoints never reveal a block.
"""
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.messaging import Conversation, Message
from app.models.user import User
from app.schemas.messaging import (
    ConversationSummary, MessageOut, MessagePerson, SendMessage, ThreadOut, UnreadOut,
)
from app.services import messaging
from app.services.email import send_email
from app.services.notifications import new_conversation_email
from app.services.public_profile import build_public_cards
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])

PAGE_SIZE = 100
PREVIEW_LENGTH = 140


def _not_found():
    return HTTPException(status_code=404, detail="Conversation not found")


def _person(db: Session, users: list[User]) -> dict[uuid.UUID, MessagePerson]:
    cards = build_public_cards(db, users)
    return {
        u.id: MessagePerson(id=u.id, first_name=u.first_name, photo_url=cards[u.id].photo_url, headline=cards[u.id].headline)
        for u in users
    }


def _out(message: Message, me: uuid.UUID, preview: bool = False) -> MessageOut:
    body = message.body
    if preview and len(body) > PREVIEW_LENGTH:
        body = body[:PREVIEW_LENGTH].rstrip() + "…"
    return MessageOut(id=message.id, from_me=message.sender_id == me, body=body, created_at=message.created_at)


def _other_or_404(db: Session, me: uuid.UUID, user_id: str) -> tuple[User, str]:
    try:
        other_uuid = uuid.UUID(user_id)
    except (ValueError, TypeError):
        raise _not_found()
    rel = messaging.relationship(db, me, other_uuid)
    if not rel:
        raise _not_found()
    return db.query(User).filter(User.id == other_uuid).first(), rel


@router.get("", response_model=list[ConversationSummary])
def list_conversations(request: Request, db: Session = Depends(get_db)):
    """Your open conversations, most recent first. Closed ones (unmatched,
    left a circle, blocked) are left out entirely."""
    user = get_current_user(request, db)
    allowed = messaging.relationships(db, user.id)
    conversations = [c for c in messaging.my_conversations(db, user.id) if messaging.other_id(c, user.id) in allowed]
    if not conversations:
        return []
    others = db.query(User).filter(User.id.in_([messaging.other_id(c, user.id) for c in conversations])).all()
    people = _person(db, others)
    unread = messaging.unread_counts(db, user.id, conversations)
    result = []
    for c in conversations:
        last = (
            db.query(Message).filter(Message.conversation_id == c.id)
            .order_by(Message.created_at.desc(), Message.id.desc()).first()
        )
        oid = messaging.other_id(c, user.id)
        result.append(ConversationSummary(
            person=people[oid], relationship=allowed[oid], last_message=_out(last, user.id, preview=True), unread=unread[c.id],
        ))
    return result


@router.get("/unread", response_model=UnreadOut)
def unread(request: Request, db: Session = Depends(get_db)):
    """For the badge in the navigation."""
    user = get_current_user(request, db)
    allowed = messaging.relationships(db, user.id)
    conversations = [c for c in messaging.my_conversations(db, user.id) if messaging.other_id(c, user.id) in allowed]
    counts = messaging.unread_counts(db, user.id, conversations)
    return UnreadOut(conversations=sum(1 for n in counts.values() if n))


@router.get("/with/{user_id}", response_model=ThreadOut)
def get_thread(user_id: str, request: Request, before: str | None = None, db: Session = Depends(get_db)):
    """The conversation with one person - the newest PAGE_SIZE messages,
    oldest first. Pass ?before=<message id> for older ones. Opening the
    latest page marks the conversation read."""
    user = get_current_user(request, db)
    other, rel = _other_or_404(db, user.id, user_id)
    person = _person(db, [other])[other.id]
    conversation = messaging.find_conversation(db, user.id, other.id)
    if not conversation:
        return ThreadOut(person=person, relationship=rel, messages=[], has_more=False)

    q = db.query(Message).filter(Message.conversation_id == conversation.id)
    if before:
        try:
            anchor = db.query(Message).filter(Message.id == uuid.UUID(before), Message.conversation_id == conversation.id).first()
        except ValueError:
            anchor = None
        if not anchor:
            raise HTTPException(status_code=400, detail="Invalid 'before' message")
        q = q.filter(Message.created_at < anchor.created_at)
    page = q.order_by(Message.created_at.desc(), Message.id.desc()).limit(PAGE_SIZE + 1).all()
    has_more = len(page) > PAGE_SIZE
    page = list(reversed(page[:PAGE_SIZE]))

    if not before:
        messaging.mark_read(conversation, user.id)
        db.commit()
    return ThreadOut(person=person, relationship=rel, messages=[_out(m, user.id) for m in page], has_more=has_more)


@router.post("/with/{user_id}", response_model=MessageOut, status_code=201)
def send_message(user_id: str, body: SendMessage, request: Request, background: BackgroundTasks, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    other, _ = _other_or_404(db, user.id, user_id)
    if messaging.sending_too_fast(db, user.id):
        raise HTTPException(status_code=429, detail="You're sending messages too quickly - please wait a moment.")

    conversation = messaging.get_or_create_conversation(db, user.id, other.id)
    is_first_message = conversation.last_message_at is None
    sent_at = messaging.now()
    message = Message(conversation_id=conversation.id, sender_id=user.id, body=body.body, created_at=sent_at)
    db.add(message)
    conversation.last_message_at = sent_at
    messaging.mark_read(conversation, user.id)  # your own message is never unread to you
    db.commit()
    db.refresh(message)

    # One email per new conversation, never per message.
    if is_first_message:
        email = new_conversation_email(db, other.id, user.id)
        if email:
            background.add_task(send_email, email)
    return _out(message, user.id)
