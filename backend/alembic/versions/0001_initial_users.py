"""initial: pgvector extension + users table

Revision ID: 0001
Revises:
Create Date: 2026-09-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

account_status_enum = postgresql.ENUM(
    "active", "suspended", "banned", "deleted", name="accountstatus"
)

# Separate reference used inside create_table: create_type=False tells
# SQLAlchemy not to attempt "CREATE TYPE" again here, since we already
# create it explicitly (with checkfirst) below. Without this, create_table
# tries to create the same enum type a second time and fails.
account_status_column_type = postgresql.ENUM(
    "active", "suspended", "banned", "deleted", name="accountstatus", create_type=False
)


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    account_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("linkedin_sub", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("birth_year", sa.Integer(), nullable=True),
        sa.Column("profile_photo_url", sa.String(), nullable=True),
        sa.Column("account_status", account_status_column_type, nullable=False, server_default="active"),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint("uq_users_linkedin_sub", "users", ["linkedin_sub"])
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.create_index("ix_users_linkedin_sub", "users", ["linkedin_sub"])
    op.create_index("ix_users_email", "users", ["email"])


def downgrade():
    op.drop_table("users")
    account_status_enum.drop(op.get_bind(), checkfirst=True)
