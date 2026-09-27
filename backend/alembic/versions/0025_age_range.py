"""add age_range and age_preference to user_social_profiles

Revision ID: 0025
Revises: 0024
Create Date: 2026-09-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None

AGE_RANGE_VALUES = ["18_24", "25_29", "30_34", "35_39", "40_49", "50_plus", "prefer_not_to_say"]


def upgrade():
    age_range_enum = postgresql.ENUM(*AGE_RANGE_VALUES, name="agerange")
    age_range_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "user_social_profiles",
        sa.Column(
            "age_range",
            postgresql.ENUM(*AGE_RANGE_VALUES, name="agerange", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        "user_social_profiles",
        sa.Column("age_range_visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "user_social_profiles",
        sa.Column("age_range_usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    # Deliberately no privacy columns for age_preference - see model docstring.
    op.add_column("user_social_profiles", sa.Column("age_preference", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("user_social_profiles", "age_preference")
    op.drop_column("user_social_profiles", "age_range_usable_for_matching")
    op.drop_column("user_social_profiles", "age_range_visible_on_profile")
    op.drop_column("user_social_profiles", "age_range")

    postgresql.ENUM(name="agerange").drop(op.get_bind(), checkfirst=True)
