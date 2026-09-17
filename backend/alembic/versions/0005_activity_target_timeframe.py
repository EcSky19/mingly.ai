"""replace user_activities.wants_to_do_now boolean with target_timeframe enum

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
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
    target_timeframe_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "user_activities",
        sa.Column("target_timeframe", target_timeframe_column_type, nullable=True),
    )
    # A user who had wants_to_do_now=true under the old boolean model most
    # closely maps to "sometime_soon" under the new one - preserves the
    # closest equivalent meaning rather than silently dropping the signal.
    op.execute(
        "UPDATE user_activities SET target_timeframe = 'sometime_soon' WHERE wants_to_do_now = true"
    )
    op.drop_column("user_activities", "wants_to_do_now")


def downgrade():
    op.add_column(
        "user_activities",
        sa.Column("wants_to_do_now", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute(
        "UPDATE user_activities SET wants_to_do_now = true WHERE target_timeframe IS NOT NULL"
    )
    op.drop_column("user_activities", "target_timeframe")
    target_timeframe_enum.drop(op.get_bind(), checkfirst=True)
