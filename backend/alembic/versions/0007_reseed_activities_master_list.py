"""add nightlife activity category, wipe and reseed activities catalog with expanded 111-item master list

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-17

"""
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

activity_category_column_type = postgresql.ENUM(
    "sports", "social_food", "entertainment", "outdoor", "casual", "pets", "nightlife",
    name="activitycategory", create_type=False,
)

# Frozen historical snapshot, NOT read from app/data/activities_starter.json
# at runtime - that file was later overwritten by migration 0009 (dog
# activity consolidation) to reflect ITS updated 107-item catalog. This
# migration must keep seeding its own original 111-item list, or
# replaying the full chain from an empty database seeds the wrong data
# at this step. Extracted from the file's exact state in commit
# d17b1ea, the commit this migration itself shipped in.
ACTIVITIES_SNAPSHOT = [
    {"name": 'After-Work Drinks', "category": 'social_food'},
    {"name": 'Arcades', "category": 'casual'},
    {"name": 'Art Classes', "category": 'casual'},
    {"name": 'Art Galleries', "category": 'entertainment'},
    {"name": 'Badminton', "category": 'sports'},
    {"name": 'Baseball / Softball', "category": 'sports'},
    {"name": 'Basketball', "category": 'sports'},
    {"name": 'Beach Days', "category": 'outdoor'},
    {"name": 'Beach Volleyball', "category": 'sports'},
    {"name": 'Billiards / Pool', "category": 'casual'},
    {"name": 'Board Game Nights', "category": 'casual'},
    {"name": 'Boating', "category": 'outdoor'},
    {"name": 'Book Clubs', "category": 'casual'},
    {"name": 'Bookstore Browsing', "category": 'casual'},
    {"name": 'Bowling', "category": 'casual'},
    {"name": 'Boxing / Martial Arts', "category": 'sports'},
    {"name": 'Breweries', "category": 'nightlife'},
    {"name": 'Brunch', "category": 'social_food'},
    {"name": 'Camping', "category": 'outdoor'},
    {"name": 'Card Games', "category": 'casual'},
    {"name": 'Chess', "category": 'casual'},
    {"name": 'Cigar Lounges', "category": 'nightlife'},
    {"name": 'Cocktail Bars', "category": 'social_food'},
    {"name": 'Coffee', "category": 'social_food'},
    {"name": 'Comedy Shows', "category": 'entertainment'},
    {"name": 'Concerts / Live Music', "category": 'entertainment'},
    {"name": 'Cooking Classes', "category": 'social_food'},
    {"name": 'Cooking Together', "category": 'social_food'},
    {"name": 'Coworking / Coffee Shops', "category": 'casual'},
    {"name": 'Cycling', "category": 'sports'},
    {"name": 'Dance Classes', "category": 'casual'},
    {"name": 'Dancing / Nightclubs', "category": 'nightlife'},
    {"name": 'Darts', "category": 'casual'},
    {"name": 'Day Trips', "category": 'outdoor'},
    {"name": 'Dinner', "category": 'social_food'},
    {"name": 'Disc Golf', "category": 'sports'},
    {"name": 'Dog-Friendly Cafes', "category": 'pets'},
    {"name": 'Dog Parks', "category": 'pets'},
    {"name": 'Dog Walks', "category": 'pets'},
    {"name": 'Drinks / Bars', "category": 'social_food'},
    {"name": 'Driving Range', "category": 'sports'},
    {"name": 'Escape Rooms', "category": 'casual'},
    {"name": 'Exploring New Neighborhoods', "category": 'outdoor'},
    {"name": 'Farmers Markets', "category": 'outdoor'},
    {"name": 'Festivals', "category": 'outdoor'},
    {"name": 'Fishing', "category": 'outdoor'},
    {"name": 'Food Festivals', "category": 'outdoor'},
    {"name": 'Food Markets', "category": 'outdoor'},
    {"name": 'Football Watch Parties', "category": 'entertainment'},
    {"name": 'Game Nights', "category": 'casual'},
    {"name": 'Golf', "category": 'sports'},
    {"name": 'Golf Simulators / Indoor Golf', "category": 'sports'},
    {"name": 'Gym / Weightlifting', "category": 'sports'},
    {"name": 'Happy Hour', "category": 'social_food'},
    {"name": 'Hiking', "category": 'outdoor'},
    {"name": 'Hiking with Dogs', "category": 'pets'},
    {"name": 'Hockey', "category": 'sports'},
    {"name": 'Ice Skating', "category": 'sports'},
    {"name": 'Investment / Stock Market Discussions', "category": 'casual'},
    {"name": 'Karaoke', "category": 'nightlife'},
    {"name": 'Kayaking', "category": 'outdoor'},
    {"name": 'Live DJ Events', "category": 'nightlife'},
    {"name": 'Lounges', "category": 'nightlife'},
    {"name": 'Mini Golf', "category": 'sports'},
    {"name": 'Movies', "category": 'entertainment'},
    {"name": 'Museums', "category": 'entertainment'},
    {"name": 'Open Mic Nights', "category": 'entertainment'},
    {"name": 'Paddleboarding', "category": 'outdoor'},
    {"name": 'Padel', "category": 'sports'},
    {"name": 'Parks', "category": 'outdoor'},
    {"name": 'Photography Walks', "category": 'outdoor'},
    {"name": 'Pickleball', "category": 'sports'},
    {"name": 'Picnics', "category": 'outdoor'},
    {"name": 'Pilates', "category": 'sports'},
    {"name": 'Poker Nights', "category": 'casual'},
    {"name": 'Pottery / Ceramics', "category": 'casual'},
    {"name": 'Pub Trivia', "category": 'casual'},
    {"name": 'Racquetball', "category": 'sports'},
    {"name": 'Rock Climbing', "category": 'sports'},
    {"name": 'Road Trips', "category": 'outdoor'},
    {"name": 'Rooftop Bars', "category": 'nightlife'},
    {"name": 'Run Clubs', "category": 'sports'},
    {"name": 'Running', "category": 'sports'},
    {"name": 'Running with Dogs', "category": 'pets'},
    {"name": 'Sailing', "category": 'outdoor'},
    {"name": 'Sauna / Spa', "category": 'casual'},
    {"name": 'Shuffleboard', "category": 'casual'},
    {"name": 'Ski Trips', "category": 'outdoor'},
    {"name": 'Skiing / Snowboarding', "category": 'sports'},
    {"name": 'Snorkeling', "category": 'outdoor'},
    {"name": 'Soccer', "category": 'sports'},
    {"name": 'Sporting Events', "category": 'entertainment'},
    {"name": 'Sports Bars', "category": 'nightlife'},
    {"name": 'Squash', "category": 'sports'},
    {"name": 'Street Fairs', "category": 'outdoor'},
    {"name": 'Surfing', "category": 'outdoor'},
    {"name": 'Swimming', "category": 'sports'},
    {"name": 'Table Tennis', "category": 'sports'},
    {"name": 'Tennis', "category": 'sports'},
    {"name": 'Theater', "category": 'entertainment'},
    {"name": 'Topgolf / Social Golf', "category": 'sports'},
    {"name": 'Trivia Nights', "category": 'casual'},
    {"name": 'Trying New Restaurants', "category": 'social_food'},
    {"name": 'Volleyball', "category": 'sports'},
    {"name": 'Volunteer Events', "category": 'casual'},
    {"name": 'Walks', "category": 'outdoor'},
    {"name": 'Watch Parties', "category": 'entertainment'},
    {"name": 'Weekend Getaways', "category": 'outdoor'},
    {"name": 'Wine Tasting', "category": 'social_food'},
    {"name": 'Workout / Fitness Classes', "category": 'sports'},
    {"name": 'Yoga', "category": 'sports'},
]


def upgrade():
    # Adding an enum value and using it in the same migration run fails
    # on Postgres ("unsafe use of new value... must be committed before
    # they can be used") unless the ADD VALUE runs in its own committed
    # transaction first - verified this against real Postgres 16 before
    # writing this migration. autocommit_block() is Alembic's documented
    # mechanism for exactly this.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE activitycategory ADD VALUE IF NOT EXISTS 'nightlife'")

    # Wipe existing activities (cascades to user_activities via FK ondelete).
    # Same safety confirmation as migration 0006 for interests - no real
    # user data exists yet.
    op.execute("DELETE FROM user_activities")
    op.execute("DELETE FROM activities")

    # Seed from the frozen snapshot above, not the current file.
    activities_table = sa.table(
        "activities",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String()),
        sa.column("category", activity_category_column_type),
    )
    op.bulk_insert(
        activities_table,
        [{"id": uuid.uuid4(), "name": a["name"], "category": a["category"]} for a in ACTIVITIES_SNAPSHOT],
    )


def downgrade():
    # No reasonable downgrade to the old 45-item list or the enum without
    # "nightlife" - Postgres doesn't support removing enum values at all.
    # This is a content/taxonomy change, not a structural one; treat as
    # forward-only. Wipes activities data if downgraded past this point.
    op.execute("DELETE FROM user_activities")
    op.execute("DELETE FROM activities")
