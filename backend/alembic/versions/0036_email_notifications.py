"""users.email_notifications: lets each person turn notification emails off

Revision ID: 0036
Revises: 0035
Create Date: 2026-10-09

"""
from alembic import op
import sqlalchemy as sa

revision = "0036"
down_revision = "0035"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("email_notifications", sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    op.drop_column("users", "email_notifications")
