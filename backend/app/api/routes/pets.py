"""
Endpoints for a user's pets. One-to-many, same pattern as
app/api/routes/education.py and languages.py.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user_pet import UserPet
from app.schemas.professional_profile import PetCreate, PetOut, PetUpdate
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/profile/pets", tags=["pets"])


@router.get("", response_model=list[PetOut])
def list_pets(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return (
        db.query(UserPet)
        .filter(UserPet.user_id == user.id)
        .order_by(UserPet.created_at)
        .all()
    )


@router.post("", response_model=PetOut, status_code=201)
def add_pet(body: PetCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    pet = UserPet(user_id=user.id, **body.model_dump())
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


@router.patch("/{pet_id}", response_model=PetOut)
def update_entry(pet_id: str, body: PetUpdate, request: Request, db: Session = Depends(get_db)):
    """Edits an existing pet, including its privacy toggles. Before this
    existed, edits to a saved pet were silently dropped by the onboarding
    page - so a privacy change like turning off 'visible on profile' was
    never actually applied."""
    user = get_current_user(request, db)
    try:
        entry_uuid = uuid.UUID(pet_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Pet not found")

    entry = db.query(UserPet).filter(UserPet.id == entry_uuid, UserPet.user_id == user.id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Pet not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{pet_id}", status_code=204)
def delete_pet(pet_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    try:
        pet_uuid = uuid.UUID(pet_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Pet not found")

    pet = (
        db.query(UserPet)
        .filter(UserPet.id == pet_uuid, UserPet.user_id == user.id)
        .first()
    )
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")

    db.delete(pet)
    db.commit()
