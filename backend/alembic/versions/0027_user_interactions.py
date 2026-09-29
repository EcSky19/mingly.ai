"""user_interactions table

Revision ID: 0027
Revises: 0026
Create Date: 2026-09-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None

ACTION_VALUES = ["dismissed", "interested"]


def upgrade():
    action_enum = postgresql.ENUM(*ACTION_VALUES, name="interactionaction")
    action_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "user_interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", postgresql.ENUM(*ACTION_VALUES, name="interactionaction", create_type=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "target_user_id", name="uq_user_interaction_pair"),
    )
    op.create_index("ix_user_interactions_user_id", "user_interactions", ["user_id"])
    op.create_index("ix_user_interactions_target_user_id", "user_interactions", ["target_user_id"])


def downgrade():
    op.drop_index("ix_user_interactions_target_user_id", table_name="user_interactions")
    op.drop_index("ix_user_interactions_user_id", table_name="user_interactions")
    op.drop_table("user_interactions")
    postgresql.ENUM(name="interactionaction").drop(op.get_bind(), checkfirst=True)
