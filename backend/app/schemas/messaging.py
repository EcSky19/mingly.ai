"""Schemas for messaging."""
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.services.messaging import MAX_MESSAGE_LENGTH


class MessagePerson(BaseModel):
    """The other person, as their public card shows them."""
    id: UUID
    first_name: str
    photo_url: Optional[str] = None
    headline: Optional[str] = None


class MessageOut(BaseModel):
    id: UUID
    from_me: bool
    body: str
    created_at: datetime


class ConversationSummary(BaseModel):
    person: MessagePerson
    relationship: Literal["match", "circle"]
    last_message: MessageOut
    unread: int


class ThreadOut(BaseModel):
    person: MessagePerson
    relationship: Literal["match", "circle"]
    messages: list[MessageOut]  # oldest first
    has_more: bool


class UnreadOut(BaseModel):
    conversations: int  # conversations with at least one unread message


class SendMessage(BaseModel):
    body: str = Field(..., max_length=MAX_MESSAGE_LENGTH)

    @field_validator("body")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message can't be empty")
        return value
