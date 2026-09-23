"""
Endpoints for a user's additional profile photos (up to 4, beyond the
LinkedIn photo). See app/models/user_photo.py and
app/services/photo_storage.py for the full design.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.activity import UserActivity
from app.models.interest import UserInterest
from app.models.user_photo import UserPhoto
from app.schemas.photos import PhotoOut
from app.services.photo_storage import delete_photo_file, save_uploaded_photo
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/profile/photos", tags=["photos"])

MAX_PHOTOS = 4


def _to_out(photo: UserPhoto) -> PhotoOut:
    return PhotoOut(
        id=photo.id,
        url=f"/api/uploads/{photo.file_path}",
        display_order=photo.display_order,
        tagged_activity_id=photo.tagged_activity_id,
        tagged_activity_name=photo.tagged_activity.name if photo.tagged_activity else None,
        tagged_interest_id=photo.tagged_interest_id,
        tagged_interest_name=photo.tagged_interest.name if photo.tagged_interest else None,
    )


@router.get("", response_model=list[PhotoOut])
def list_photos(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    photos = (
        db.query(UserPhoto)
        .filter(UserPhoto.user_id == user.id)
        .order_by(UserPhoto.display_order)
        .all()
    )
    return [_to_out(p) for p in photos]


@router.post("", response_model=PhotoOut, status_code=201)
async def upload_photo(
    request: Request,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    tagged_activity_id: Optional[str] = Form(default=None),
    tagged_interest_id: Optional[str] = Form(default=None),
):
    user = get_current_user(request, db)

    existing_count = db.query(UserPhoto).filter(UserPhoto.user_id == user.id).count()
    if existing_count >= MAX_PHOTOS:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_PHOTOS} photos allowed")

    if tagged_activity_id and tagged_interest_id:
        raise HTTPException(status_code=400, detail="A photo can be tagged to an activity or an interest, not both")

    activity_uuid = None
    interest_uuid = None

    if tagged_activity_id:
        try:
            activity_uuid = uuid.UUID(tagged_activity_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tagged_activity_id")
        # Must be one of THIS user's own LOVED (is_top_pick) activities -
        # not just any catalog activity - see model docstring for why.
        loved = (
            db.query(UserActivity)
            .filter(
                UserActivity.user_id == user.id,
                UserActivity.activity_id == activity_uuid,
                UserActivity.is_top_pick == True,  # noqa: E712
            )
            .first()
        )
        if not loved:
            raise HTTPException(status_code=400, detail="You can only tag photos to activities you've loved")

    if tagged_interest_id:
        try:
            interest_uuid = uuid.UUID(tagged_interest_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tagged_interest_id")
        loved = (
            db.query(UserInterest)
            .filter(
                UserInterest.user_id == user.id,
                UserInterest.interest_id == interest_uuid,
                UserInterest.is_top_pick == True,  # noqa: E712
            )
            .first()
        )
        if not loved:
            raise HTTPException(status_code=400, detail="You can only tag photos to interests you've loved")

    file_path = await save_uploaded_photo(str(user.id), file)

    photo = UserPhoto(
        user_id=user.id,
        file_path=file_path,
        display_order=existing_count,
        tagged_activity_id=activity_uuid,
        tagged_interest_id=interest_uuid,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return _to_out(photo)


@router.delete("/{photo_id}", status_code=204)
def delete_photo(photo_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    try:
        photo_uuid = uuid.UUID(photo_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Photo not found")

    photo = (
        db.query(UserPhoto)
        .filter(UserPhoto.id == photo_uuid, UserPhoto.user_id == user.id)
        .first()
    )
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    delete_photo_file(photo.file_path)
    db.delete(photo)
    db.commit()
