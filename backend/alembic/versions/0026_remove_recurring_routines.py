"""remove user_recurring_routines table

Revision ID: 0026
Revises: 0025
Create Date: 2026-09-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None

TIME_WINDOW_VALUES = ["morning", "afternoon", "evening", "late_night", "flexible"]


def upgrade():
    op.drop_index("ix_user_recurring_routines_user_id", table_name="user_recurring_routines")
    op.drop_table("user_recurring_routines")
    postgresql.ENUM(name="timewindow").drop(op.get_bind(), checkfirst=True)


def downgrade():
    time_window_enum = postgresql.ENUM(*TIME_WINDOW_VALUES, name="timewindow")
    time_window_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "user_recurring_routines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("activity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("days_of_week", sa.JSON(), nullable=True),
        sa.Column("time_window", postgresql.ENUM(*TIME_WINDOW_VALUES, name="timewindow", create_type=False), nullable=True),
        sa.Column("location_context", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_recurring_routines_user_id", "user_recurring_routines", ["user_id"])
