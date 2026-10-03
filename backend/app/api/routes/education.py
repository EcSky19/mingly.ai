"""
Endpoints for a user's education history. One-to-many by design - see
app/models/user_education.py for why.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user_education import UserEducation
from app.schemas.professional_profile import EducationEntryCreate, EducationEntryOut, EducationEntryUpdate
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/profile/education", tags=["education"])


@router.get("", response_model=list[EducationEntryOut])
def list_education(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    entries = (
        db.query(UserEducation)
        .filter(UserEducation.user_id == user.id)
        .order_by(UserEducation.created_at)
        .all()
    )
    return entries


@router.post("", response_model=EducationEntryOut, status_code=201)
def add_education(body: EducationEntryCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    entry = UserEducation(user_id=user.id, **body.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.patch("/{entry_id}", response_model=EducationEntryOut)
def update_entry(entry_id: str, body: EducationEntryUpdate, request: Request, db: Session = Depends(get_db)):
    """Edits an existing education entry, including its privacy toggles. Before this
    existed, edits to a saved education entry were silently dropped by the onboarding
    page - so a privacy change like turning off 'visible on profile' was
    never actually applied."""
    user = get_current_user(request, db)
    try:
        entry_uuid = uuid.UUID(entry_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Education entry not found")

    entry = db.query(UserEducation).filter(UserEducation.id == entry_uuid, UserEducation.user_id == user.id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Education entry not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_education(entry_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    try:
        entry_uuid = uuid.UUID(entry_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Education entry not found")

    entry = (
        db.query(UserEducation)
        .filter(UserEducation.id == entry_uuid, UserEducation.user_id == user.id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Education entry not found")

    db.delete(entry)
    db.commit()
