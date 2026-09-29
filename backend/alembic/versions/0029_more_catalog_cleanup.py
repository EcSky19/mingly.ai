"""remove Sailing interest (Sailing activity already exists), add Sushi
Nights and Video Gaming activities, add Comics & Trading Cards interest

Revision ID: 0029
Revises: 0028
Create Date: 2026-09-29

"""
from alembic import op
import sqlalchemy as sa

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None


def upgrade():
    # Same pattern as the Golf/Poker carry-forward in 0028: rather than
    # checking production first and doing a second round trip, build the
    # protection in by default - cheap either way, and 0028 already
    # proved real users can have exactly this kind of selection.
    op.execute(
        sa.text(
            """
            INSERT INTO user_activities (id, user_id, activity_id, is_top_pick, visible_on_profile)
            SELECT gen_random_uuid(), ui.user_id, a.id, ui.is_top_pick, ui.visible_on_profile
            FROM user_interests ui
            JOIN interests i ON i.id = ui.interest_id
            JOIN activities a ON a.name = 'Sailing'
            WHERE i.name = 'Sailing'
            AND NOT EXISTS (
                SELECT 1 FROM user_activities ua2 WHERE ua2.user_id = ui.user_id AND ua2.activity_id = a.id
            )
            """
        )
    )
    op.execute(sa.text("DELETE FROM interests WHERE name = 'Sailing'"))

    op.execute(
        sa.text(
            "INSERT INTO activities (id, name, category) VALUES (gen_random_uuid(), 'Sushi Nights', 'social_food')"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO activities (id, name, category) VALUES (gen_random_uuid(), 'Video Gaming', 'casual')"
        )
    )
    op.execute(
        sa.text("INSERT INTO interests (id, name) VALUES (gen_random_uuid(), 'Comics & Trading Cards')")
    )


def downgrade():
    op.execute(sa.text("DELETE FROM interests WHERE name = 'Comics & Trading Cards'"))
    op.execute(sa.text("DELETE FROM activities WHERE name = 'Video Gaming'"))
    op.execute(sa.text("DELETE FROM activities WHERE name = 'Sushi Nights'"))
    op.execute(sa.text("INSERT INTO interests (id, name) VALUES (gen_random_uuid(), 'Sailing')"))
