"""
Endpoints for a user's locations. One-to-many, free for everyone - see
docs/location-design.md.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user_location import UserLocation
from app.schemas.discovery_profile import LocationCreate, LocationOut, LocationUpdate
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/profile/locations", tags=["locations"])


@router.get("", response_model=list[LocationOut])
def list_locations(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return db.query(UserLocation).filter(UserLocation.user_id == user.id).all()


@router.post("", response_model=LocationOut, status_code=201)
def add_location(body: LocationCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)

    # Exactly one location should be primary. If this one is marked
    # primary, un-mark any existing primary rather than ending up with
    # zero or multiple - see docs/location-design.md.
    if body.is_primary:
        db.query(UserLocation).filter(
            UserLocation.user_id == user.id, UserLocation.is_primary == True  # noqa: E712
        ).update({"is_primary": False})

    location = UserLocation(user_id=user.id, **body.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@router.patch("/{location_id}", response_model=LocationOut)
def update_location(location_id: str, body: LocationUpdate, request: Request, db: Session = Depends(get_db)):
    """Edits an existing location (city, label, travel radius, primary).
    Before this existed there was no way to change a saved location at
    all - the onboarding page silently dropped every edit to one."""
    user = get_current_user(request, db)
    try:
        location_uuid = uuid.UUID(location_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Location not found")

    location = (
        db.query(UserLocation)
        .filter(UserLocation.id == location_uuid, UserLocation.user_id == user.id)
        .first()
    )
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    data = body.model_dump(exclude_unset=True)
    if data.get("is_primary"):
        # Exactly one primary, same rule as creating a location
        db.query(UserLocation).filter(
            UserLocation.user_id == user.id,
            UserLocation.id != location.id,
            UserLocation.is_primary == True,  # noqa: E712
        ).update({"is_primary": False})
    for field, value in data.items():
        setattr(location, field, value)

    db.commit()
    db.refresh(location)
    return location


@router.delete("/{location_id}", status_code=204)
def delete_location(location_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    try:
        location_uuid = uuid.UUID(location_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Location not found")

    location = (
        db.query(UserLocation)
        .filter(UserLocation.id == location_uuid, UserLocation.user_id == user.id)
        .first()
    )
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    db.delete(location)
    db.commit()
