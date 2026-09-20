"""remove neighborhood from user_locations

Revision ID: 0017
Revises: 0016
Create Date: 2026-09-21

"""
from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("user_locations", "neighborhood")


def downgrade():
    op.add_column("user_locations", sa.Column("neighborhood", sa.String(), nullable=True))
