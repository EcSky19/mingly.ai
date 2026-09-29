"""user_locations, interests catalog + user_interests, activities catalog + user_activities

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-16

"""
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

# Frozen historical snapshots, NOT read from app/data/*.json at runtime.
# Those files were later overwritten by migrations 0006/0007/0009 to
# reflect THEIR OWN updated catalogs - this migration must keep using
# the exact data it originally seeded with, or replaying the full chain
# from an empty database breaks (confirmed: re-running from scratch
# failed here with "invalid input value for enum activitycategory:
# nightlife" - the file had already been evolved by 0007 - because
# 'nightlife' isn't added as a valid enum value until migration 0007,
# several steps after this one). Extracted from the file's exact state
# in commit c57e8d7, the commit this migration itself shipped in.
INTERESTS_SNAPSHOT = [
    'AI & Technology', 'Startups & Entrepreneurship', 'Investing & Finance', 'Sports', 'Movies & TV',
    'Music', 'Live Music & Concerts', 'Books & Reading', 'Travel', 'History',
    'Fitness & Wellness', 'Cooking & Food', 'Photography', 'Art & Design', 'Fashion',
    'Politics & Current Events', 'Science', 'Philosophy', 'Psychology', 'Gaming',
    'Board Games', 'Comedy', 'Theater', 'Dance', 'Wine & Cocktails',
    'Coffee Culture', 'Nature & Outdoors', 'Sustainability & Environment', 'Volunteering', 'Real Estate',
    'Cars & Motorsports', 'Personal Finance', 'Crypto & Web3', 'Writing', 'Podcasts',
    'Meditation & Mindfulness', 'Fashion & Style', 'Architecture', 'Languages & Linguistics', 'Space & Astronomy',
    'Entrepreneurship', 'Marketing & Branding', 'Social Impact', 'Education & Learning', 'Pets & Animals',
    'DIY & Home Improvement', 'Fitness Competitions', 'Running', 'Yoga', 'Spirituality & Religion',
]

ACTIVITIES_SNAPSHOT = [
    {"name": 'Running', "category": 'sports'},
    {"name": 'Gym / Weightlifting', "category": 'sports'},
    {"name": 'Tennis', "category": 'sports'},
    {"name": 'Pickleball', "category": 'sports'},
    {"name": 'Golf', "category": 'sports'},
    {"name": 'Basketball', "category": 'sports'},
    {"name": 'Soccer', "category": 'sports'},
    {"name": 'Skiing / Snowboarding', "category": 'sports'},
    {"name": 'Rock Climbing', "category": 'sports'},
    {"name": 'Cycling', "category": 'sports'},
    {"name": 'Swimming', "category": 'sports'},
    {"name": 'Yoga', "category": 'sports'},
    {"name": 'Boxing / Martial Arts', "category": 'sports'},
    {"name": 'Coffee', "category": 'social_food'},
    {"name": 'Brunch', "category": 'social_food'},
    {"name": 'Dinner', "category": 'social_food'},
    {"name": 'Trying New Restaurants', "category": 'social_food'},
    {"name": 'Drinks / Bars', "category": 'social_food'},
    {"name": 'Cocktail Bars', "category": 'social_food'},
    {"name": 'Cooking Together', "category": 'social_food'},
    {"name": 'Wine Tasting', "category": 'social_food'},
    {"name": 'Concerts / Live Music', "category": 'entertainment'},
    {"name": 'Comedy Shows', "category": 'entertainment'},
    {"name": 'Movies', "category": 'entertainment'},
    {"name": 'Museums', "category": 'entertainment'},
    {"name": 'Sporting Events', "category": 'entertainment'},
    {"name": 'Theater', "category": 'entertainment'},
    {"name": 'Karaoke', "category": 'entertainment'},
    {"name": 'Trivia Nights', "category": 'entertainment'},
    {"name": 'Parks', "category": 'outdoor'},
    {"name": 'Beach', "category": 'outdoor'},
    {"name": 'Hiking', "category": 'outdoor'},
    {"name": 'Camping', "category": 'outdoor'},
    {"name": 'Picnics', "category": 'outdoor'},
    {"name": 'Walks', "category": 'casual'},
    {"name": 'Coworking / Coffee Shops', "category": 'casual'},
    {"name": 'Exploring New Neighborhoods', "category": 'casual'},
    {"name": 'Board Game Nights', "category": 'casual'},
    {"name": 'Bookstore Browsing', "category": 'casual'},
    {"name": 'Dog Walks', "category": 'pets'},
    {"name": 'Dog Parks', "category": 'pets'},
    {"name": 'Dog-Friendly Cafes', "category": 'pets'},
    {"name": 'Hiking with Dogs', "category": 'pets'},
    {"name": 'Running with Dogs', "category": 'pets'},
    {"name": 'Meeting Other Dog Owners', "category": 'pets'},
]

activity_category_enum = postgresql.ENUM(
    "sports", "social_food", "entertainment", "outdoor", "casual", "pets",
    name="activitycategory",
)
activity_category_column_type = postgresql.ENUM(
    "sports", "social_food", "entertainment", "outdoor", "casual", "pets",
    name="activitycategory", create_type=False,
)

skill_level_enum = postgresql.ENUM(
    "beginner", "intermediate", "advanced", "competitive", "not_applicable",
    name="skilllevel",
)
skill_level_column_type = postgresql.ENUM(
    "beginner", "intermediate", "advanced", "competitive", "not_applicable",
    name="skilllevel", create_type=False,
)

activity_style_enum = postgresql.ENUM(
    "casual_social", "fitness_focused", "competitive", "exploratory",
    name="activitystyle",
)
activity_style_column_type = postgresql.ENUM(
    "casual_social", "fitness_focused", "competitive", "exploratory",
    name="activitystyle", create_type=False,
)

desired_frequency_enum = postgresql.ENUM(
    "rarely", "monthly", "weekly", "multiple_times_per_week",
    name="desiredfrequency",
)
desired_frequency_column_type = postgresql.ENUM(
    "rarely", "monthly", "weekly", "multiple_times_per_week",
    name="desiredfrequency", create_type=False,
)

interest_strength_enum = postgresql.ENUM(
    "casual", "moderate", "high", name="intereststrength",
)
interest_strength_column_type = postgresql.ENUM(
    "casual", "moderate", "high", name="intereststrength", create_type=False,
)

preferred_group_size_enum = postgresql.ENUM(
    "one_on_one", "small_group", "either", name="preferredgroupsize",
)
preferred_group_size_column_type = postgresql.ENUM(
    "one_on_one", "small_group", "either", name="preferredgroupsize", create_type=False,
)


def upgrade():
    # --- Locations ---
    op.create_table(
        "user_locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("metro", sa.String(), nullable=True),
        sa.Column("neighborhood", sa.String(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("travel_radius_miles", sa.Integer(), nullable=True),
        sa.Column("transport_preferences", sa.String(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("label", sa.String(), nullable=True),
    )
    op.create_index("ix_user_locations_user_id", "user_locations", ["user_id"])

    # --- Interests ---
    op.create_table(
        "interests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
    )
    op.create_unique_constraint("uq_interests_name", "interests", ["name"])
    op.create_index("ix_interests_name", "interests", ["name"])

    op.create_table(
        "user_interests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interest_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_top_pick", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("priority_rank", sa.Integer(), nullable=True),
        sa.Column("visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_user_interests_user_id", "user_interests", ["user_id"])

    # --- Activities ---
    activity_category_enum.create(op.get_bind(), checkfirst=True)
    skill_level_enum.create(op.get_bind(), checkfirst=True)
    activity_style_enum.create(op.get_bind(), checkfirst=True)
    desired_frequency_enum.create(op.get_bind(), checkfirst=True)
    interest_strength_enum.create(op.get_bind(), checkfirst=True)
    preferred_group_size_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", activity_category_column_type, nullable=False),
    )
    op.create_unique_constraint("uq_activities_name", "activities", ["name"])
    op.create_index("ix_activities_name", "activities", ["name"])

    op.create_table(
        "user_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("activity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interest_strength", interest_strength_column_type, nullable=True),
        sa.Column("skill_level", skill_level_column_type, nullable=True),
        sa.Column("activity_style", activity_style_column_type, nullable=True),
        sa.Column("desired_frequency", desired_frequency_column_type, nullable=True),
        sa.Column("preferred_group_size", preferred_group_size_column_type, nullable=True),
        sa.Column("is_top_pick", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("wants_to_do_now", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_user_activities_user_id", "user_activities", ["user_id"])

    # --- Seed catalogs (from the frozen snapshots above, not the current file) ---
    interests_table = sa.table("interests", sa.column("id", postgresql.UUID(as_uuid=True)), sa.column("name", sa.String()))
    op.bulk_insert(interests_table, [{"id": uuid.uuid4(), "name": n} for n in INTERESTS_SNAPSHOT])

    activities_table = sa.table(
        "activities",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String()),
        sa.column("category", activity_category_column_type),
    )
    op.bulk_insert(activities_table, [{"id": uuid.uuid4(), "name": a["name"], "category": a["category"]} for a in ACTIVITIES_SNAPSHOT])


def downgrade():
    op.drop_index("ix_user_activities_user_id", table_name="user_activities")
    op.drop_table("user_activities")
    op.drop_index("ix_activities_name", table_name="activities")
    op.drop_table("activities")

    preferred_group_size_enum.drop(op.get_bind(), checkfirst=True)
    interest_strength_enum.drop(op.get_bind(), checkfirst=True)
    desired_frequency_enum.drop(op.get_bind(), checkfirst=True)
    activity_style_enum.drop(op.get_bind(), checkfirst=True)
    skill_level_enum.drop(op.get_bind(), checkfirst=True)
    activity_category_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_user_interests_user_id", table_name="user_interests")
    op.drop_table("user_interests")
    op.drop_index("ix_interests_name", table_name="interests")
    op.drop_table("interests")

    op.drop_index("ix_user_locations_user_id", table_name="user_locations")
    op.drop_table("user_locations")
