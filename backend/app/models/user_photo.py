"""
A user's additional profile photos - up to 4, beyond the LinkedIn photo
already captured on the User model. Each can optionally be tagged to
one of the user's own LOVED activities or interests (is_top_pick=True
rows only - see app/models/activity.py, app/models/interest.py), since
the point is showing real evidence of things the user said they
genuinely love, not just any selection.

A photo can be tagged to an activity OR an interest, never both -
enforced at the schema layer (see app/schemas/photos.py), not a DB
constraint, for simplicity.

Files are stored on local server disk (bind-mounted via the existing
./backend:/app Docker volume, so they survive container rebuilds) and
served via a dedicated static route - see app/main.py.
"""
import uuid

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class UserPhoto(Base):
    __tablename__ = "user_photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    file_path = Column(String, nullable=False)  # relative path under the uploads directory
    display_order = Column(Integer, nullable=False, default=0)

    tagged_activity_id = Column(UUID(as_uuid=True), ForeignKey("activities.id", ondelete="SET NULL"), nullable=True)
    tagged_interest_id = Column(UUID(as_uuid=True), ForeignKey("interests.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="photos")
    tagged_activity = relationship("Activity")
    tagged_interest = relationship("Interest")
