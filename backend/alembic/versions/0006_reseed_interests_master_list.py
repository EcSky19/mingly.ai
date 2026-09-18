"""wipe and reseed interests catalog with expanded 80-item master list

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-17

"""
import json
import uuid
from pathlib import Path

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "data"


def upgrade():
    # Wipe existing interests (cascades to user_interests via FK ondelete).
    # Confirmed with the product owner this is safe - no real user data
    # exists yet, only throwaway test selections. See docs/roadmap.md
    # and the interests/activities taxonomy expansion discussion.
    op.execute("DELETE FROM user_interests")
    op.execute("DELETE FROM interests")

    with open(DATA_DIR / "interests_starter.json") as f:
        interest_names = json.load(f)

    interests_table = sa.table(
        "interests", sa.column("id", postgresql.UUID(as_uuid=True)), sa.column("name", sa.String())
    )
    op.bulk_insert(interests_table, [{"id": uuid.uuid4(), "name": n} for n in interest_names])


def downgrade():
    # No reasonable downgrade to the old 50-item list - this is a content
    # change, not a structural one. Wipes to empty; re-run migration 0004
    # manually if the old list is genuinely needed back.
    op.execute("DELETE FROM user_interests")
    op.execute("DELETE FROM interests")
