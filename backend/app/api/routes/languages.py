"""
Endpoints for a user's spoken languages. One-to-many, same pattern as
app/api/routes/education.py.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user_language import UserLanguage
from app.schemas.professional_profile import LanguageEntryCreate, LanguageEntryOut, LanguageEntryUpdate
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/profile/languages", tags=["languages"])


@router.get("", response_model=list[LanguageEntryOut])
def list_languages(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return (
        db.query(UserLanguage)
        .filter(UserLanguage.user_id == user.id)
        .order_by(UserLanguage.created_at)
        .all()
    )


@router.post("", response_model=LanguageEntryOut, status_code=201)
def add_language(body: LanguageEntryCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    entry = UserLanguage(user_id=user.id, **body.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.patch("/{entry_id}", response_model=LanguageEntryOut)
def update_entry(entry_id: str, body: LanguageEntryUpdate, request: Request, db: Session = Depends(get_db)):
    """Edits an existing language, including its privacy toggles. Before this
    existed, edits to a saved language were silently dropped by the onboarding
    page - so a privacy change like turning off 'visible on profile' was
    never actually applied."""
    user = get_current_user(request, db)
    try:
        entry_uuid = uuid.UUID(entry_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Language not found")

    entry = db.query(UserLanguage).filter(UserLanguage.id == entry_uuid, UserLanguage.user_id == user.id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Language not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_language(entry_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    try:
        entry_uuid = uuid.UUID(entry_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Language not found")

    entry = (
        db.query(UserLanguage)
        .filter(UserLanguage.id == entry_uuid, UserLanguage.user_id == user.id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Language not found")

    db.delete(entry)
    db.commit()
