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
    # 2 real users have "Golf" or "Poker" as an interest right now (checked
    # against production before writing this, not assumed) - rather than
    # letting those selections silently vanish when the interest rows are
    # removed below, carry them forward to the equivalent Activity first.
    # NOT EXISTS guards against creating a duplicate for anyone who
    # already separately selected the activity too.
    op.execute(
        sa.text(
            """
            INSERT INTO user_activities (id, user_id, activity_id, is_top_pick, visible_on_profile)
            SELECT gen_random_uuid(), ui.user_id, a.id, ui.is_top_pick, ui.visible_on_profile
            FROM user_interests ui
            JOIN interests i ON i.id = ui.interest_id
            JOIN activities a ON a.name = 'Golf'
            WHERE i.name = 'Golf'
            AND NOT EXISTS (
                SELECT 1 FROM user_activities ua2 WHERE ua2.user_id = ui.user_id AND ua2.activity_id = a.id
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO user_activities (id, user_id, activity_id, is_top_pick, visible_on_profile)
            SELECT gen_random_uuid(), ui.user_id, a.id, ui.is_top_pick, ui.visible_on_profile
            FROM user_interests ui
            JOIN interests i ON i.id = ui.interest_id
            JOIN activities a ON a.name = 'Poker Nights'
            WHERE i.name = 'Poker'
            AND NOT EXISTS (
                SELECT 1 FROM user_activities ua2 WHERE ua2.user_id = ui.user_id AND ua2.activity_id = a.id
            )
            """
        )
    )

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
    # Note: this does not attempt to remove the 2 user_activities rows
    # that upgrade() may have auto-created (Golf, Poker Nights) - there's
    # no way to distinguish those from a real selection the user made in
    # the meantime, so leaving them in place is the safer default. Not
    # destructive either way, just a known limitation of downgrading a
    # data migration.
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
