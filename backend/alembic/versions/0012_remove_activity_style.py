"""remove activity_style from user_activities

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

activity_style_enum = postgresql.ENUM(
    "casual_social", "fitness_focused", "competitive", "exploratory",
    name="activitystyle",
)
activity_style_column_type = postgresql.ENUM(
    "casual_social", "fitness_focused", "competitive", "exploratory",
    name="activitystyle", create_type=False,
)


def upgrade():
    op.drop_column("user_activities", "activity_style")
    activity_style_enum.drop(op.get_bind(), checkfirst=True)


def downgrade():
    activity_style_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("user_activities", sa.Column("activity_style", activity_style_column_type, nullable=True))
