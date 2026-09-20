"""user_social_profiles table: lifestyle, career orientation, social preferences

Revision ID: 0015
Revises: 0014
Create Date: 2026-09-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def _enum(name, values):
    return postgresql.ENUM(*values, name=name)


ENUMS = {
    "careerorientation": [
        "career_focused_building_life_outside", "very_career_driven", "entrepreneurial",
        "grad_or_professional_school", "established_expanding_social_life", "balanced",
    ],
    "earlybirdnightowl": ["early_bird", "night_owl", "either"],
    "activitylevel": ["active", "moderate", "relaxed"],
    "drinkingpreference": ["non_drinker", "social_drinker", "regular_drinker", "prefer_not_to_say"],
    "goingoutfrequency": ["rarely", "sometimes", "often", "very_often"],
    "indooroutdoorpreference": ["indoor", "outdoor", "either"],
    "weekdayweekendpreference": ["weekdays", "weekends", "either"],
    "socialcadence": [
        "multiple_times_per_week", "about_once_per_week", "a_few_times_per_month", "occasionally",
    ],
    "planningstyle": [
        "spontaneous", "a_day_or_two_ahead", "several_days_ahead", "about_a_week_ahead", "flexible",
    ],
    "meetingpreference": [
        "one_on_one", "small_groups", "either", "prefer_bringing_someone_known",
    ],
}


def upgrade():
    for name, values in ENUMS.items():
        _enum(name, values).create(op.get_bind(), checkfirst=True)

    op.create_table(
        "user_social_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("career_orientation", postgresql.ENUM(*ENUMS["careerorientation"], name="careerorientation", create_type=False), nullable=True),
        sa.Column("career_qualities", sa.JSON(), nullable=True),
        sa.Column("early_bird_night_owl", postgresql.ENUM(*ENUMS["earlybirdnightowl"], name="earlybirdnightowl", create_type=False), nullable=True),
        sa.Column("activity_level", postgresql.ENUM(*ENUMS["activitylevel"], name="activitylevel", create_type=False), nullable=True),
        sa.Column("drinking_preference", postgresql.ENUM(*ENUMS["drinkingpreference"], name="drinkingpreference", create_type=False), nullable=True),
        sa.Column("going_out_frequency", postgresql.ENUM(*ENUMS["goingoutfrequency"], name="goingoutfrequency", create_type=False), nullable=True),
        sa.Column("indoor_outdoor_preference", postgresql.ENUM(*ENUMS["indooroutdoorpreference"], name="indooroutdoorpreference", create_type=False), nullable=True),
        sa.Column("weekday_weekend_preference", postgresql.ENUM(*ENUMS["weekdayweekendpreference"], name="weekdayweekendpreference", create_type=False), nullable=True),
        sa.Column("social_cadence", postgresql.ENUM(*ENUMS["socialcadence"], name="socialcadence", create_type=False), nullable=True),
        sa.Column("planning_style", postgresql.ENUM(*ENUMS["planningstyle"], name="planningstyle", create_type=False), nullable=True),
        sa.Column("meeting_preference", postgresql.ENUM(*ENUMS["meetingpreference"], name="meetingpreference", create_type=False), nullable=True),
        sa.Column("social_environment", sa.JSON(), nullable=True),
        sa.Column("social_goals", sa.JSON(), nullable=True),
        sa.Column("visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_unique_constraint("uq_user_social_profiles_user_id", "user_social_profiles", ["user_id"])
    op.create_index("ix_user_social_profiles_user_id", "user_social_profiles", ["user_id"])


def downgrade():
    op.drop_index("ix_user_social_profiles_user_id", table_name="user_social_profiles")
    op.drop_table("user_social_profiles")
    for name in ENUMS:
        _enum(name, ENUMS[name]).drop(op.get_bind(), checkfirst=True)
