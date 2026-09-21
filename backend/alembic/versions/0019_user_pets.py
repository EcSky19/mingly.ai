"""user_pets table

Revision ID: 0019
Revises: 0018
Create Date: 2026-09-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None

PET_TYPE_VALUES = ["dog", "cat", "other"]
PET_SIZE_VALUES = ["small", "medium", "large"]
PET_ACTIVITY_LEVEL_VALUES = ["low", "moderate", "high"]


def upgrade():
    pet_type_enum = postgresql.ENUM(*PET_TYPE_VALUES, name="pettype")
    pet_size_enum = postgresql.ENUM(*PET_SIZE_VALUES, name="petsize")
    pet_activity_level_enum = postgresql.ENUM(*PET_ACTIVITY_LEVEL_VALUES, name="petactivitylevel")
    pet_type_enum.create(op.get_bind(), checkfirst=True)
    pet_size_enum.create(op.get_bind(), checkfirst=True)
    pet_activity_level_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "user_pets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pet_type", postgresql.ENUM(*PET_TYPE_VALUES, name="pettype", create_type=False), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("size", postgresql.ENUM(*PET_SIZE_VALUES, name="petsize", create_type=False), nullable=True),
        sa.Column("activity_level", postgresql.ENUM(*PET_ACTIVITY_LEVEL_VALUES, name="petactivitylevel", create_type=False), nullable=True),
        sa.Column("comfortable_with_other_dogs", sa.Boolean(), nullable=True),
        sa.Column("visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_pets_user_id", "user_pets", ["user_id"])


def downgrade():
    op.drop_index("ix_user_pets_user_id", table_name="user_pets")
    op.drop_table("user_pets")

    postgresql.ENUM(name="petactivitylevel").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="petsize").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="pettype").drop(op.get_bind(), checkfirst=True)
