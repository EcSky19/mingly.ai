"""
Endpoints for a user's recurring routines. One-to-many, with a PATCH
for partial updates (e.g. pausing a routine via is_active) in addition
to the usual list/add/delete pattern - see
app/models/user_recurring_routine.py.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.activity import Activity
from app.models.user_recurring_routine import UserRecurringRoutine
from app.schemas.recurring_routines import RoutineCreate, RoutineOut, RoutineUpdate
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/profile/routines", tags=["routines"])


def _to_out(routine: UserRecurringRoutine) -> RoutineOut:
    return RoutineOut(
        id=routine.id,
        activity_id=routine.activity_id,
        activity_name=routine.activity.name,
        days_of_week=routine.days_of_week,
        time_window=routine.time_window,
        location_context=routine.location_context,
        is_active=routine.is_active,
        visible_on_profile=routine.visible_on_profile,
        usable_for_matching=routine.usable_for_matching,
    )


@router.get("", response_model=list[RoutineOut])
def list_routines(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    routines = (
        db.query(UserRecurringRoutine)
        .filter(UserRecurringRoutine.user_id == user.id)
        .order_by(UserRecurringRoutine.created_at)
        .all()
    )
    return [_to_out(r) for r in routines]


@router.post("", response_model=RoutineOut, status_code=201)
def add_routine(body: RoutineCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)

    activity = db.query(Activity).filter(Activity.id == body.activity_id).first()
    if not activity:
        raise HTTPException(status_code=400, detail="Invalid activity_id")

    routine = UserRecurringRoutine(user_id=user.id, **body.model_dump())
    db.add(routine)
    db.commit()
    db.refresh(routine)
    return _to_out(routine)


@router.patch("/{routine_id}", response_model=RoutineOut)
def update_routine(
    routine_id: str, body: RoutineUpdate, request: Request, db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    try:
        routine_uuid = uuid.UUID(routine_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Routine not found")

    routine = (
        db.query(UserRecurringRoutine)
        .filter(UserRecurringRoutine.id == routine_uuid, UserRecurringRoutine.user_id == user.id)
        .first()
    )
    if not routine:
        raise HTTPException(status_code=404, detail="Routine not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(routine, field, value)

    db.commit()
    db.refresh(routine)
    return _to_out(routine)


@router.delete("/{routine_id}", status_code=204)
def delete_routine(routine_id: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    try:
        routine_uuid = uuid.UUID(routine_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=404, detail="Routine not found")

    routine = (
        db.query(UserRecurringRoutine)
        .filter(UserRecurringRoutine.id == routine_uuid, UserRecurringRoutine.user_id == user.id)
        .first()
    )
    if not routine:
        raise HTTPException(status_code=404, detail="Routine not found")

    db.delete(routine)
    db.commit()
