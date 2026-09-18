"""consolidate 5 separate dog activities into one "Activities with Dogs"

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-17

"""
import json
import uuid
from pathlib import Path

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "data"

activity_category_column_type = postgresql.ENUM(
    "sports", "social_food", "entertainment", "outdoor", "casual", "pets", "nightlife",
    name="activitycategory", create_type=False,
)


def upgrade():
    # Same wipe-and-reseed pattern as migrations 0006/0007 - confirmed
    # safe (no real user selections exist yet), consistent with the
    # ongoing taxonomy cleanup from this session.
    op.execute("DELETE FROM user_activity_subtags")
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

    # Re-seed subtags too, since wiping activities cascaded them away
    # and their activity_id foreign keys need to point at the new rows.
    with open(DATA_DIR / "activity_subtags_starter.json") as f:
        subtags_by_activity = json.load(f)

    conn = op.get_bind()
    subtags_table = sa.table(
        "activity_subtags",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("activity_id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String()),
    )
    rows_to_insert = []
    for activity_name, subtag_names in subtags_by_activity.items():
        result = conn.execute(
            sa.select(activities_table.c.id).where(activities_table.c.name == activity_name)
        ).first()
        if result is None:
            raise RuntimeError(
                f"Activity '{activity_name}' not found in catalog - cannot seed its subtags"
            )
        activity_id = result[0]
        for subtag_name in subtag_names:
            rows_to_insert.append({"id": uuid.uuid4(), "activity_id": activity_id, "name": subtag_name})

    if rows_to_insert:
        op.bulk_insert(subtags_table, rows_to_insert)


def downgrade():
    op.execute("DELETE FROM user_activity_subtags")
    op.execute("DELETE FROM user_activities")
    op.execute("DELETE FROM activities")
