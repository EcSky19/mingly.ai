"""user_languages table

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

language_proficiency_enum = postgresql.ENUM(
    "native", "fluent", "conversational", "learning", name="languageproficiency",
)
language_proficiency_column_type = postgresql.ENUM(
    "native", "fluent", "conversational", "learning", name="languageproficiency", create_type=False,
)


def upgrade():
    language_proficiency_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "user_languages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("proficiency", language_proficiency_column_type, nullable=True),
        sa.Column("visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_languages_user_id", "user_languages", ["user_id"])


def downgrade():
    op.drop_index("ix_user_languages_user_id", table_name="user_languages")
    op.drop_table("user_languages")
    language_proficiency_enum.drop(op.get_bind(), checkfirst=True)
