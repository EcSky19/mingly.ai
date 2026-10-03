"""backfill onboarding_completed for users who already went through onboarding

Revision ID: 0030
Revises: 0029
Create Date: 2026-10-02

Nothing ever set onboarding_completed to true before the
/api/auth/onboarding-complete endpoint existed - the flag was read by the
eligibility filter and the login redirect, but never written - so every
existing user is stuck at false no matter how much they filled in. This
marks complete anyone with at least one saved location: the clearest
evidence they went through onboarding, and matching can't work without
a location anyway (the distance gate needs one).
"""
from alembic import op

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE users SET onboarding_completed = true
        WHERE onboarding_completed = false
        AND EXISTS (SELECT 1 FROM user_locations l WHERE l.user_id = users.id)
        """
    )


def downgrade():
    # Deliberately a no-op: after this runs, there's no way to tell a
    # backfilled row apart from someone who completed onboarding normally
    # afterwards, so reverting would wrongly reset real completions.
    pass
