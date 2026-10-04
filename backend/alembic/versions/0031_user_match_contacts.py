"""user_match_contacts table - optional contact info visible only to mutual matches

Revision ID: 0031
Revises: 0030
Create Date: 2026-10-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_match_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("instagram", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", name="uq_user_match_contacts_user_id"),
    )
    op.create_index("ix_user_match_contacts_user_id", "user_match_contacts", ["user_id"])


def downgrade():
    op.drop_index("ix_user_match_contacts_user_id", table_name="user_match_contacts")
    op.drop_table("user_match_contacts")
