"""remove target_timeframe from user_activities

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

target_timeframe_enum = postgresql.ENUM(
    "ready_now", "sometime_soon", "when_season_right", "no_rush",
    name="targettimeframe",
)
target_timeframe_column_type = postgresql.ENUM(
    "ready_now", "sometime_soon", "when_season_right", "no_rush",
    name="targettimeframe", create_type=False,
)


def upgrade():
    op.drop_column("user_activities", "target_timeframe")
    target_timeframe_enum.drop(op.get_bind(), checkfirst=True)


def downgrade():
    target_timeframe_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("user_activities", sa.Column("target_timeframe", target_timeframe_column_type, nullable=True))
