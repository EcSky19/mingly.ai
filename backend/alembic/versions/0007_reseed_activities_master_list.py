"""add nightlife activity category, wipe and reseed activities catalog with expanded 111-item master list

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-17

"""
import json
import uuid
from pathlib import Path

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "data"

activity_category_column_type = postgresql.ENUM(
    "sports", "social_food", "entertainment", "outdoor", "casual", "pets", "nightlife",
    name="activitycategory", create_type=False,
)


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

    with open(DATA_DIR / "activities_starter.json") as f:
        activities = json.load(f)

    activities_table = sa.table(
        "activities",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String()),
        sa.column("category", activity_category_column_type),
    )
    op.bulk_insert(
        activities_table,
        [{"id": uuid.uuid4(), "name": a["name"], "category": a["category"]} for a in activities],
    )


def downgrade():
    # No reasonable downgrade to the old 45-item list or the enum without
    # "nightlife" - Postgres doesn't support removing enum values at all.
    # This is a content/taxonomy change, not a structural one; treat as
    # forward-only. Wipes activities data if downgraded past this point.
    op.execute("DELETE FROM user_activities")
    op.execute("DELETE FROM activities")
