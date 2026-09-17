"""
Endpoints for browsing the interests catalog and setting a user's
selected interests.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.interest import Interest, UserInterest
from app.schemas.discovery_profile import InterestCatalogOut, UserInterestOut, UserInterestSet
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/profile/interests", tags=["interests"])
catalog_router = APIRouter(prefix="/api/catalog/interests", tags=["catalog"])

MAX_TOP_PICKS = 5


@catalog_router.get("", response_model=list[InterestCatalogOut])
def list_interest_catalog(db: Session = Depends(get_db)):
    return db.query(Interest).order_by(Interest.name).all()


@router.get("", response_model=list[UserInterestOut])
def get_user_interests(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    rows = db.query(UserInterest).filter(UserInterest.user_id == user.id).all()
    return [
        UserInterestOut(
            interest_id=r.interest_id,
            name=r.interest.name,
            is_top_pick=r.is_top_pick,
            visible_on_profile=r.visible_on_profile,
        )
        for r in rows
    ]


@router.put("", response_model=list[UserInterestOut])
def set_user_interests(body: UserInterestSet, request: Request, db: Session = Depends(get_db)):
    """Replaces the user's full interest selection in one call - simpler
    and less error-prone for a multi-select UI than incremental
    add/remove calls per checkbox toggle."""
    user = get_current_user(request, db)

    if len(body.top_pick_ids) > MAX_TOP_PICKS:
        raise HTTPException(status_code=400, detail=f"At most {MAX_TOP_PICKS} top picks allowed")
    if not set(body.top_pick_ids).issubset(set(body.interest_ids)):
        raise HTTPException(status_code=400, detail="Top picks must be a subset of selected interests")

    # Confirm every id actually exists in the catalog, so a bad client
    # request can't create orphaned rows pointing at nothing.
    valid_ids = {
        row.id for row in db.query(Interest.id).filter(Interest.id.in_(body.interest_ids)).all()
    }
    if valid_ids != set(body.interest_ids):
        raise HTTPException(status_code=400, detail="One or more interest_ids are not valid")

    db.query(UserInterest).filter(UserInterest.user_id == user.id).delete()

    for interest_id in body.interest_ids:
        db.add(
            UserInterest(
                user_id=user.id,
                interest_id=interest_id,
                is_top_pick=interest_id in body.top_pick_ids,
                visible_on_profile=body.visible_on_profile,
            )
        )
    db.commit()

    rows = db.query(UserInterest).filter(UserInterest.user_id == user.id).all()
    return [
        UserInterestOut(
            interest_id=r.interest_id,
            name=r.interest.name,
            is_top_pick=r.is_top_pick,
            visible_on_profile=r.visible_on_profile,
        )
        for r in rows
    ]
