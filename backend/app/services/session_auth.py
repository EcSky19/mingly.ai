"""
Shared helper for looking up the current authenticated user from the
session. Centralized so every protected route handles this the same
way, rather than each route re-implementing (and potentially
re-breaking) the same logic.
"""
import uuid

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models.user import User


def get_current_user(request: Request, db: Session) -> User:
    """Returns the authenticated User, or raises 401.

    Session stores user_id as a plain string (see auth.py callback).
    The User.id column is a native UUID type, which requires an actual
    uuid.UUID object for reliable comparison - passing a raw string
    works by coincidence under some database backends but not others
    (confirmed failing under SQLite during testing), so we convert
    explicitly here rather than relying on implicit coercion.
    """
    raw_user_id = request.session.get("user_id")
    if not raw_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_uuid = uuid.UUID(raw_user_id)
    except (ValueError, TypeError):
        # Malformed session data - treat as unauthenticated, not a 500.
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
