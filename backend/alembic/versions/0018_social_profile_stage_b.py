"""add spending_preference, city_circle_status, comfortable_with_dogs to user_social_profiles

Revision ID: 0018
Revises: 0017
Create Date: 2026-09-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

SPENDING_PREFERENCE_VALUES = [
    "inexpensive", "moderate", "occasional_splurge", "premium", "depends_on_activity",
]
CITY_CIRCLE_STATUS_VALUES = [
    "new_here", "know_some_want_to_expand", "have_circle_want_more", "mainly_activity_partners",
]


def upgrade():
    spending_enum = postgresql.ENUM(*SPENDING_PREFERENCE_VALUES, name="spendingpreference")
    city_circle_enum = postgresql.ENUM(*CITY_CIRCLE_STATUS_VALUES, name="citycirclestatus")
    spending_enum.create(op.get_bind(), checkfirst=True)
    city_circle_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "user_social_profiles",
        sa.Column(
            "spending_preference",
            postgresql.ENUM(*SPENDING_PREFERENCE_VALUES, name="spendingpreference", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        "user_social_profiles",
        sa.Column(
            "city_circle_status",
            postgresql.ENUM(*CITY_CIRCLE_STATUS_VALUES, name="citycirclestatus", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        "user_social_profiles",
        sa.Column("comfortable_with_dogs", sa.Boolean(), nullable=True),
    )


def downgrade():
    op.drop_column("user_social_profiles", "comfortable_with_dogs")
    op.drop_column("user_social_profiles", "city_circle_status")
    op.drop_column("user_social_profiles", "spending_preference")

    postgresql.ENUM(name="citycirclestatus").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="spendingpreference").drop(op.get_bind(), checkfirst=True)
