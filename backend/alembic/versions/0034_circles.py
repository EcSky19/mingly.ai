"""circles: connections, requests, invite codes, mutual-connection setting

Revision ID: 0034
Revises: 0033
Create Date: 2026-10-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0034"
down_revision = "0033"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "circle_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_a_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_b_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(), nullable=False, server_default="invite"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_a_id", "user_b_id", name="uq_circle_connections_pair"),
        sa.CheckConstraint("user_a_id < user_b_id", name="ck_circle_connections_canonical_order"),
    )
    op.create_index("ix_circle_connections_user_a_id", "circle_connections", ["user_a_id"])
    op.create_index("ix_circle_connections_user_b_id", "circle_connections", ["user_b_id"])

    status = postgresql.ENUM("pending", "accepted", "declined", name="circlerequeststatus")
    status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "circle_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("from_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", postgresql.ENUM(name="circlerequeststatus", create_type=False), nullable=False, server_default="pending"),
        sa.Column("source", sa.String(), nullable=False, server_default="invite_link"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("from_user_id", "to_user_id", name="uq_circle_requests_pair"),
    )
    op.create_index("ix_circle_requests_from_user_id", "circle_requests", ["from_user_id"])
    op.create_index("ix_circle_requests_to_user_id", "circle_requests", ["to_user_id"])

    op.create_table(
        "user_invite_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_invite_codes_code", "user_invite_codes", ["code"])

    op.add_column("users", sa.Column("show_as_mutual_connection", sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    op.drop_column("users", "show_as_mutual_connection")
    op.drop_index("ix_user_invite_codes_code", table_name="user_invite_codes")
    op.drop_table("user_invite_codes")
    op.drop_index("ix_circle_requests_to_user_id", table_name="circle_requests")
    op.drop_index("ix_circle_requests_from_user_id", table_name="circle_requests")
    op.drop_table("circle_requests")
    postgresql.ENUM(name="circlerequeststatus").drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_circle_connections_user_b_id", table_name="circle_connections")
    op.drop_index("ix_circle_connections_user_a_id", table_name="circle_connections")
    op.drop_table("circle_connections")
