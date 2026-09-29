"""remove 23 interests redundant with existing activities; remove
duplicate Pub Trivia (Trivia Nights already exists); add Bar Hopping
activity

Revision ID: 0028
Revises: 0027
Create Date: 2026-09-29

"""
from alembic import op
import sqlalchemy as sa

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None

# Each of these already exists as an Activity, either literally (e.g.
# "Golf") or conceptually ("Chess & Strategy Games" -> "Chess"), or was
# an umbrella covering several activities already in the catalog
# ("Racket Sports" -> Tennis, Padel, Pickleball, Table Tennis, etc).
# Keeping both asked the same underlying question twice.
INTERESTS_TO_REMOVE = [
    "Golf", "Padel", "Pickleball", "Running", "Tennis", "Table Tennis", "Yoga", "Card Games",
    "Skiing & Snowboarding", "Live Music & Concerts", "Chess & Strategy Games", "Board Games",
    "Dance", "Fishing & Angling", "Poker", "Theater & Performing Arts", "Comedy",
    "Boating & Sailing", "Volunteering & Community Service", "Cigars & Cigar Culture",
    "Dining & Restaurants", "Racket Sports", "Culture & Museums",
]


def upgrade():
    op.execute(
        sa.text("DELETE FROM interests WHERE name = ANY(:names)").bindparams(names=INTERESTS_TO_REMOVE)
    )
    # "Trivia Nights" already exists as a separate, redundant entry
    # alongside "Pub Trivia" - a genuine pre-existing catalog duplicate,
    # unrelated to anything else in this migration, discovered while
    # attempting a rename here. Deleting "Pub Trivia" (0 real user
    # selections reference it, confirmed before writing this) achieves
    # the same intended end state as a rename would have.
    op.execute(sa.text("DELETE FROM activities WHERE name = 'Pub Trivia'"))
    op.execute(
        sa.text(
            "INSERT INTO activities (id, name, category) VALUES (gen_random_uuid(), 'Bar Hopping', 'nightlife')"
        )
    )


def downgrade():
    op.execute(sa.text("DELETE FROM activities WHERE name = 'Bar Hopping'"))
    op.execute(
        sa.text(
            "INSERT INTO activities (id, name, category) VALUES (gen_random_uuid(), 'Pub Trivia', 'casual')"
        )
    )
    for name in INTERESTS_TO_REMOVE:
        op.execute(
            sa.text("INSERT INTO interests (id, name) VALUES (gen_random_uuid(), :name)").bindparams(name=name)
        )
