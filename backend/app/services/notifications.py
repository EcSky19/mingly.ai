"""
Notification emails: a new match, and someone joining your circle.

Each function only *builds* the email (or returns None when it shouldn't be
sent); routes hand the result to a background task that sends it after the
response has gone out, so a slow mail server never slows the app down.

An email is only built when the recipient:
  - has an active account (never email suspended or banned people),
  - hasn't turned notification emails off in Settings, and
  - isn't blocked by / blocking the other person.
Only the other person's first name is ever included.
"""
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import AccountStatus, User
from app.services.email import Email
from app.services.safety import is_blocked


def _footer() -> str:
    return (
        "\n\n-\nMingly - build the life around your career.\n"
        f"You're getting this because email notifications are on. Turn them off in Settings: {settings.APP_URL}/settings\n"
    )


def _people(db: Session, recipient_id: UUID, other_id: UUID) -> tuple[User, User] | None:
    recipient = db.query(User).filter(User.id == recipient_id).first()
    other = db.query(User).filter(User.id == other_id).first()
    if not recipient or not other or not recipient.email:
        return None
    if recipient.account_status != AccountStatus.active or other.account_status != AccountStatus.active:
        return None
    if not recipient.email_notifications or is_blocked(db, recipient_id, other_id):
        return None
    return recipient, other


def new_match_email(db: Session, recipient_id: UUID, other_id: UUID) -> Email | None:
    """To the person who said Connect first - the second person saw the
    match moment on screen already."""
    people = _people(db, recipient_id, other_id)
    if not people:
        return None
    recipient, other = people
    return Email(
        to=recipient.email,
        subject=f"You and {other.first_name} matched on Mingly",
        text=(
            f"Hi {recipient.first_name},\n\n"
            f"{other.first_name} wants to connect too - you're a match.\n\n"
            f"See how to reach each other: {settings.APP_URL}/matches"
            + _footer()
        ),
    )


def circle_joined_email(db: Session, recipient_id: UUID, other_id: UUID) -> Email | None:
    """To the inviter, when someone accepts their circle invite."""
    people = _people(db, recipient_id, other_id)
    if not people:
        return None
    recipient, other = people
    return Email(
        to=recipient.email,
        subject=f"{other.first_name} joined your circle on Mingly",
        text=(
            f"Hi {recipient.first_name},\n\n"
            f"{other.first_name} accepted your invite and is now in your circle. "
            "Friends of your circle will see you both as a mutual connection (if you allow it), "
            "which helps everyone meet people they can trust.\n\n"
            f"See your circle: {settings.APP_URL}/circle"
            + _footer()
        ),
    )
