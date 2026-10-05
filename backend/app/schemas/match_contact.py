"""Schemas for the optional 'how matches can reach you' contact info."""
import re
from typing import Optional

from pydantic import BaseModel, field_validator

# Only genuine LinkedIn profile links (optionally with a country subdomain),
# so a match's link can never point anywhere unexpected.
LINKEDIN_RE = re.compile(
    r"^(?:https?://)?(?:www\.|[a-z]{2}\.)?linkedin\.com/in/([^/?#\s]+)(?:[/?#].*)?$", re.IGNORECASE
)
LINKEDIN_SLUG_RE = re.compile(r"^[A-Za-z0-9\-_%.]{3,100}$")
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
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    instagram: Optional[str] = None

    @field_validator("linkedin_url")
    @classmethod
    def _linkedin(cls, v):
        """Accepts however people copy it - with or without https/www, a
        country subdomain, trailing slash, or tracking parameters - and
        stores one canonical form."""
        v = _blank_to_none(v)
        if v is None:
            return v
        m = LINKEDIN_RE.match(v)
        if not m or not LINKEDIN_SLUG_RE.match(m.group(1)):
            raise ValueError("Paste your LinkedIn profile link, like linkedin.com/in/yourname")
        return f"https://www.linkedin.com/in/{m.group(1).lower()}"

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
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None
    instagram: Optional[str] = None
