"""remove preferred_group_size from user_activities

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

preferred_group_size_enum = postgresql.ENUM(
    "one_on_one", "small_group", "either", name="preferredgroupsize",
)
preferred_group_size_column_type = postgresql.ENUM(
    "one_on_one", "small_group", "either", name="preferredgroupsize", create_type=False,
)


def upgrade():
    op.drop_column("user_activities", "preferred_group_size")
    preferred_group_size_enum.drop(op.get_bind(), checkfirst=True)


def downgrade():
    preferred_group_size_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("user_activities", sa.Column("preferred_group_size", preferred_group_size_column_type, nullable=True))
