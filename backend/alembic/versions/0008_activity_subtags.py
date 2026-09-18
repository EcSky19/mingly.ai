"""activity_subtags and user_activity_subtags tables, seeded for a handful of activities

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-17

"""
import json
import uuid
from pathlib import Path

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "data"


def upgrade():
    op.create_table(
        "activity_subtags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("activity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
    )
    op.create_index("ix_activity_subtags_activity_id", "activity_subtags", ["activity_id"])

    op.create_table(
        "user_activity_subtags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_activity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user_activities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subtag_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("activity_subtags.id", ondelete="CASCADE"), nullable=False),
    )
    op.create_index("ix_user_activity_subtags_user_activity_id", "user_activity_subtags", ["user_activity_id"])

    # Honest scope: seeded only for the handful of activities where
    # subtags were explicitly designed (see app/data/activity_subtags_starter.json
    # and app/models/activity.py's ActivitySubtag docstring) - not all 111
    # catalog activities.
    conn = op.get_bind()
    with open(DATA_DIR / "activity_subtags_starter.json") as f:
        subtags_by_activity = json.load(f)

    activities_table = sa.table(
        "activities", sa.column("id", postgresql.UUID(as_uuid=True)), sa.column("name", sa.String())
    )
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
            # Shouldn't happen if migration 0007 ran first and the name
            # matches exactly, but fail loudly rather than silently skip
            # if the activities catalog and this seed data ever drift apart.
            raise RuntimeError(
                f"Activity '{activity_name}' not found in catalog - cannot seed its subtags"
            )
        activity_id = result[0]
        for subtag_name in subtag_names:
            rows_to_insert.append({"id": uuid.uuid4(), "activity_id": activity_id, "name": subtag_name})

    if rows_to_insert:
        op.bulk_insert(subtags_table, rows_to_insert)


def downgrade():
    op.drop_index("ix_user_activity_subtags_user_activity_id", table_name="user_activity_subtags")
    op.drop_table("user_activity_subtags")
    op.drop_index("ix_activity_subtags_activity_id", table_name="activity_subtags")
    op.drop_table("activity_subtags")
