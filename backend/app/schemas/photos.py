"""
Schemas for the additional profile photos feature (up to 4, each
optionally tagged to a loved activity or interest).
"""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, model_validator


class PhotoTagRequest(BaseModel):
    """Form fields accompanying a photo upload - the file itself is a
    separate multipart field, handled directly in the route."""
    tagged_activity_id: Optional[UUID] = None
    tagged_interest_id: Optional[UUID] = None

    @model_validator(mode="after")
    def one_tag_max(self):
        if self.tagged_activity_id and self.tagged_interest_id:
            raise ValueError("A photo can be tagged to an activity or an interest, not both")
        return self


class PhotoOut(BaseModel):
    id: UUID
    url: str
    display_order: int
    tagged_activity_id: Optional[UUID] = None
    tagged_activity_name: Optional[str] = None
    tagged_interest_id: Optional[UUID] = None
    tagged_interest_name: Optional[str] = None
