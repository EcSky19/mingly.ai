"""add is_user_submitted flag to interests/activities, add 'other' activity category

Revision ID: 0016
Revises: 0015
Create Date: 2026-09-20

"""
from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade():
    # Same gotcha as migration 0007 - adding an enum value and using it
    # in the same transaction fails on Postgres. Not strictly needed
    # here since this migration doesn't insert any 'other'-category
    # rows itself, but using autocommit_block anyway for consistency
    # and safety against future migrations in the same deploy.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE activitycategory ADD VALUE IF NOT EXISTS 'other'")

    op.add_column(
        "interests",
        sa.Column("is_user_submitted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "activities",
        sa.Column("is_user_submitted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column("activities", "is_user_submitted")
    op.drop_column("interests", "is_user_submitted")
    # Postgres doesn't support removing enum values - 'other' stays in
    # the type even on downgrade, same limitation noted in migration 0007.
