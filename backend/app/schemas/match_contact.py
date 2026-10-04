"""Schemas for the optional 'how matches can reach you' contact info."""
import re
from typing import Optional

from pydantic import BaseModel, field_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_ALLOWED_RE = re.compile(r"^[0-9+\-().\s]+$")
INSTAGRAM_RE = re.compile(r"^[A-Za-z0-9._]{1,30}$")


def _blank_to_none(v):
    if v is None:
        return None
    v = v.strip()
    return v or None


class MatchContactUpdate(BaseModel):
    """Partial update: omitted fields are left alone; null or an empty
    string clears a field."""
    email: Optional[str] = None
    phone: Optional[str] = None
    instagram: Optional[str] = None

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        v = _blank_to_none(v)
        if v is not None and (len(v) > 254 or not EMAIL_RE.match(v)):
            raise ValueError("That doesn't look like a valid email address")
        return v

    @field_validator("phone")
    @classmethod
    def _phone(cls, v):
        v = _blank_to_none(v)
        if v is None:
            return v
        digits = sum(c.isdigit() for c in v)
        if not PHONE_ALLOWED_RE.match(v) or not 7 <= digits <= 15:
            raise ValueError("That doesn't look like a valid phone number")
        return v

    @field_validator("instagram")
    @classmethod
    def _instagram(cls, v):
        v = _blank_to_none(v)
        if v is None:
            return v
        v = v.lstrip("@")
        if not INSTAGRAM_RE.match(v):
            raise ValueError("Instagram handles are letters, numbers, periods, and underscores (max 30)")
        return v


class MatchContactOut(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    instagram: Optional[str] = None
