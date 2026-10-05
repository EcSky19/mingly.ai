"""add 'later' (Decide Later) to the interaction action enum

Revision ID: 0032
Revises: 0031
Create Date: 2026-10-05

"""
from alembic import op

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE interactionaction ADD VALUE IF NOT EXISTS 'later'")


def downgrade():
    # Postgres can't remove a value from an enum type, so the value itself
    # stays; deleting the rows that use it means nothing depends on it.
    op.execute("DELETE FROM user_interactions WHERE action = 'later'")
