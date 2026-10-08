"""
Trust & safety: blocks, reports, and an audit log of admin actions.

Blocking is two-way in effect: once either person blocks the other, they
disappear from each other's Discover, matches, circles, and requests -
enforced centrally (see app/services/safety.py), so no feature, ranking
change, or future model can reintroduce them.
"""
import enum
import uuid

from sqlalchemy import CheckConstraint, Column, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.session import Base


class UserBlock(Base):
    __tablename__ = "user_blocks"
    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_user_blocks_pair"),
        CheckConstraint("blocker_id <> blocked_id", name="ck_user_blocks_not_self"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blocker_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    blocked_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReportReason(str, enum.Enum):
    harassment = "harassment"
    fake_profile = "fake_profile"
    spam = "spam"
    safety_concern = "safety_concern"
    misrepresented_profile = "misrepresented_profile"
    inappropriate_behavior = "inappropriate_behavior"
    unwanted_romantic_behavior = "unwanted_romantic_behavior"
    recruiting_or_referrals = "recruiting_or_referrals"
    sales_outreach = "sales_outreach"
    other = "other"


class ReportStatus(str, enum.Enum):
    open = "open"
    actioned = "actioned"      # an admin took action on the reported account
    dismissed = "dismissed"    # reviewed, no action needed


class UserReport(Base):
    """A report about another user. The reported person is never told who
    reported them. If the reporter later deletes their account, the report
    is kept for moderation history with the reporter cleared."""
    __tablename__ = "user_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reported_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(Enum(ReportReason), nullable=False)
    details = Column(Text, nullable=True)
    status = Column(Enum(ReportStatus), nullable=False, default=ReportStatus.open)
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class AdminAction(Base):
    """Every moderation action, for accountability: who did what to whom."""
    __tablename__ = "admin_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    target_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("user_reports.id", ondelete="SET NULL"), nullable=True)
    action = Column(String, nullable=False)  # suspend, unsuspend, ban, dismiss_report
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
