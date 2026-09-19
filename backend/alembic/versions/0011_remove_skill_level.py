"""remove skill_level from user_activities

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

skill_level_enum = postgresql.ENUM(
    "beginner", "intermediate", "advanced", "competitive", "not_applicable",
    name="skilllevel",
)
skill_level_column_type = postgresql.ENUM(
    "beginner", "intermediate", "advanced", "competitive", "not_applicable",
    name="skilllevel", create_type=False,
)


def upgrade():
    op.drop_column("user_activities", "skill_level")
    skill_level_enum.drop(op.get_bind(), checkfirst=True)


def downgrade():
    skill_level_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("user_activities", sa.Column("skill_level", skill_level_column_type, nullable=True))
