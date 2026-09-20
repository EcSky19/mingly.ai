"""
A user's locations - one-to-many, free for everyone (not a premium
feature). See docs/location-design.md for the full reasoning.
"""
import uuid

from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserLocation(Base):
    __tablename__ = "user_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    city = Column(String, nullable=True)
    metro = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    travel_radius_miles = Column(Integer, nullable=True)
    transport_preferences = Column(String, nullable=True)  # free text for MVP, e.g. "walking, subway"

    is_primary = Column(Boolean, nullable=False, default=False)
    label = Column(String, nullable=True)  # user's own words, e.g. "Work", "Home"

    user = relationship("User", backref="locations")
