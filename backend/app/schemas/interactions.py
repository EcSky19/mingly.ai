"""
Schemas for recording one user's action toward another. See
app/models/user_interaction.py for the design reasoning.
"""
from uuid import UUID
from pydantic import BaseModel

from app.models.user_interaction import InteractionAction


class InteractionRequest(BaseModel):
    target_user_id: UUID
    action: InteractionAction


class InteractionOut(BaseModel):
    id: UUID
    target_user_id: UUID
    action: InteractionAction

    class Config:
        from_attributes = True
