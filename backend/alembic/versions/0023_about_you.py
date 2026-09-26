"""add gender_identity and mingle_preference to user_social_profiles

Revision ID: 0023
Revises: 0022
Create Date: 2026-09-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None

GENDER_IDENTITY_VALUES = ["woman", "man", "non_binary", "self_describe", "prefer_not_to_say"]


def upgrade():
    gender_identity_enum = postgresql.ENUM(*GENDER_IDENTITY_VALUES, name="genderidentity")
    gender_identity_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "user_social_profiles",
        sa.Column(
            "gender_identity",
            postgresql.ENUM(*GENDER_IDENTITY_VALUES, name="genderidentity", create_type=False),
            nullable=True,
        ),
    )
    op.add_column("user_social_profiles", sa.Column("gender_identity_description", sa.String(), nullable=True))
    op.add_column(
        "user_social_profiles",
        sa.Column("gender_identity_visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "user_social_profiles",
        sa.Column("gender_identity_usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    # Deliberately no privacy columns for mingle_preference - see model docstring.
    op.add_column("user_social_profiles", sa.Column("mingle_preference", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("user_social_profiles", "mingle_preference")
    op.drop_column("user_social_profiles", "gender_identity_usable_for_matching")
    op.drop_column("user_social_profiles", "gender_identity_visible_on_profile")
    op.drop_column("user_social_profiles", "gender_identity_description")
    op.drop_column("user_social_profiles", "gender_identity")

    postgresql.ENUM(name="genderidentity").drop(op.get_bind(), checkfirst=True)
