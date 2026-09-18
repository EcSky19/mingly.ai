"""
Endpoints for browsing the activities catalog and setting a user's
selected activities with per-activity context.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.activity import Activity, UserActivity
from app.schemas.discovery_profile import ActivityCatalogOut, UserActivityOut, UserActivitySet
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/profile/activities", tags=["activities"])
catalog_router = APIRouter(prefix="/api/catalog/activities", tags=["catalog"])

MAX_TOP_PICKS = 3  # "top 3 activities they genuinely want to do this month" - root PRD section 20


def _to_out(row: UserActivity) -> UserActivityOut:
    return UserActivityOut(
        activity_id=row.activity_id,
        name=row.activity.name,
        category=row.activity.category,
        interest_strength=row.interest_strength,
        skill_level=row.skill_level,
        activity_style=row.activity_style,
        desired_frequency=row.desired_frequency,
        preferred_group_size=row.preferred_group_size,
        is_top_pick=row.is_top_pick,
        target_timeframe=row.target_timeframe,
        visible_on_profile=row.visible_on_profile,
    )


@catalog_router.get("", response_model=list[ActivityCatalogOut])
def list_activity_catalog(db: Session = Depends(get_db)):
    # Sort in application code, not via DB ORDER BY - Postgres's default
    # locale collation compares punctuation/spaces differently than plain
    # codepoint order (confirmed: production sorted "Ski Trips" after
    # "Skiing / Snowboarding", which ORDER BY name alone got wrong).
    # Sorting here guarantees identical, predictable behavior regardless
    # of the database's locale settings.
    activities = db.query(Activity).all()
    return sorted(activities, key=lambda a: a.name)


@router.get("", response_model=list[UserActivityOut])
def get_user_activities(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    rows = db.query(UserActivity).filter(UserActivity.user_id == user.id).all()
    return [_to_out(r) for r in rows]


@router.put("", response_model=list[UserActivityOut])
def set_user_activities(body: UserActivitySet, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)

    top_pick_count = sum(1 for a in body.activities if a.is_top_pick)
    if top_pick_count > MAX_TOP_PICKS:
        raise HTTPException(status_code=400, detail=f"At most {MAX_TOP_PICKS} top picks allowed")

    activity_ids = [a.activity_id for a in body.activities]
    valid_ids = {
        row.id for row in db.query(Activity.id).filter(Activity.id.in_(activity_ids)).all()
    }
    if valid_ids != set(activity_ids):
        raise HTTPException(status_code=400, detail="One or more activity_ids are not valid")

    db.query(UserActivity).filter(UserActivity.user_id == user.id).delete()

    for a in body.activities:
        db.add(
            UserActivity(
                user_id=user.id,
                activity_id=a.activity_id,
                interest_strength=a.interest_strength,
                skill_level=a.skill_level,
                activity_style=a.activity_style,
                desired_frequency=a.desired_frequency,
                preferred_group_size=a.preferred_group_size,
                is_top_pick=a.is_top_pick,
                target_timeframe=a.target_timeframe,
                visible_on_profile=a.visible_on_profile,
            )
        )
    db.commit()

    rows = db.query(UserActivity).filter(UserActivity.user_id == user.id).all()
    return [_to_out(r) for r in rows]
