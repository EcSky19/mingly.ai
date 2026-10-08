"""
Admin-only moderation: review reports, dismiss them, and suspend, unsuspend,
or ban accounts. Every action is written to admin_actions. Non-admins get a
plain 404, so the admin area isn't discoverable.
"""
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.safety import AdminAction, ReportStatus, UserReport
from app.models.user import AccountStatus, User
from app.services.session_auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db)
    if not user.is_admin:
        raise HTTPException(status_code=404, detail="Not found")
    return user


class AdminPerson(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    account_status: str


class AdminReport(BaseModel):
    id: uuid.UUID
    reason: str
    details: Optional[str] = None
    status: str
    admin_note: Optional[str] = None
    created_at: Optional[datetime] = None
    reporter: Optional[AdminPerson] = None  # None if the reporter has since deleted their account
    reported: AdminPerson
    reports_against_reported: int  # all reports ever filed about this person


class DismissBody(BaseModel):
    note: Optional[str] = Field(default=None, max_length=2000)


class StatusBody(BaseModel):
    status: Literal["active", "suspended", "banned"]
    note: Optional[str] = Field(default=None, max_length=2000)
    report_id: Optional[uuid.UUID] = None  # the report this action resolves, if any


def _person(u: User) -> AdminPerson:
    return AdminPerson(id=u.id, first_name=u.first_name, last_name=u.last_name, email=u.email,
                       account_status=getattr(u.account_status, "value", u.account_status))


@router.get("/reports", response_model=list[AdminReport])
def list_reports(status: Literal["open", "actioned", "dismissed", "all"] = "open",
                 admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    q = db.query(UserReport)
    if status != "all":
        q = q.filter(UserReport.status == ReportStatus(status))
    reports = q.order_by(UserReport.created_at.desc()).all()
    people_ids = {r.reported_id for r in reports} | {r.reporter_id for r in reports if r.reporter_id}
    people = {u.id: u for u in db.query(User).filter(User.id.in_(people_ids)).all()} if people_ids else {}
    counts = dict(
        db.query(UserReport.reported_id, func.count(UserReport.id))
        .filter(UserReport.reported_id.in_({r.reported_id for r in reports}))
        .group_by(UserReport.reported_id)
        .all()
    ) if reports else {}
    return [
        AdminReport(
            id=r.id, reason=r.reason.value, details=r.details, status=r.status.value, admin_note=r.admin_note,
            created_at=r.created_at,
            reporter=_person(people[r.reporter_id]) if r.reporter_id in people else None,
            reported=_person(people[r.reported_id]),
            reports_against_reported=counts.get(r.reported_id, 1),
        )
        for r in reports if r.reported_id in people
    ]


def _report_or_404(db: Session, report_id) -> UserReport:
    report = db.query(UserReport).filter(UserReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/reports/{report_id}/dismiss")
def dismiss_report(report_id: uuid.UUID, body: DismissBody, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    report = _report_or_404(db, report_id)
    report.status = ReportStatus.dismissed
    report.admin_note = body.note
    report.resolved_at = datetime.now(timezone.utc)
    db.add(AdminAction(admin_id=admin.id, target_user_id=report.reported_id, report_id=report.id, action="dismiss_report", note=body.note))
    db.commit()
    return {"ok": True}


@router.post("/users/{user_id}/status")
def set_status(user_id: uuid.UUID, body: StatusBody, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You can't change your own account status")
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    report = _report_or_404(db, body.report_id) if body.report_id else None
    if report and report.reported_id != target.id:
        raise HTTPException(status_code=400, detail="That report is about a different user")

    target.account_status = AccountStatus(body.status)
    action = {"active": "unsuspend", "suspended": "suspend", "banned": "ban"}[body.status]
    if report:
        report.status = ReportStatus.actioned
        report.admin_note = body.note
        report.resolved_at = datetime.now(timezone.utc)
    db.add(AdminAction(admin_id=admin.id, target_user_id=target.id, report_id=report.id if report else None, action=action, note=body.note))
    db.commit()
    return {"ok": True, "account_status": body.status}
