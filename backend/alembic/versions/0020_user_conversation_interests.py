"""user_conversation_interests table

Revision ID: 0020
Revises: 0019
Create Date: 2026-09-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_conversation_interests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interest_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_user_conversation_interests_user_id", "user_conversation_interests", ["user_id"])


def downgrade():
    op.drop_index("ix_user_conversation_interests_user_id", table_name="user_conversation_interests")
    op.drop_table("user_conversation_interests")
