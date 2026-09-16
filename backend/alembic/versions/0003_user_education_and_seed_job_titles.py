"""user_education table (replaces flat education fields), industries note, seed job titles starter set

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-16

"""
import json
import uuid
from pathlib import Path

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "data"


def upgrade():
    # --- Replace flat single-entry education fields with a proper
    # one-to-many table. Early enough (one real test user) that a clean
    # drop-and-recreate is worth it over a data migration - see
    # docs/professional-profile-design.md and app/models/user_education.py.
    op.drop_column("professional_profiles", "school")
    op.drop_column("professional_profiles", "school_visible_on_profile")
    op.drop_column("professional_profiles", "school_usable_for_matching")
    op.drop_column("professional_profiles", "degree")
    op.drop_column("professional_profiles", "degree_visible_on_profile")
    op.drop_column("professional_profiles", "degree_usable_for_matching")
    op.drop_column("professional_profiles", "field_of_study")
    op.drop_column("professional_profiles", "field_of_study_visible_on_profile")
    op.drop_column("professional_profiles", "field_of_study_usable_for_matching")
    op.drop_column("professional_profiles", "graduation_year")
    op.drop_column("professional_profiles", "graduation_year_visible_on_profile")
    op.drop_column("professional_profiles", "graduation_year_usable_for_matching")

    op.create_table(
        "user_education",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("school", sa.String(), nullable=True),
        sa.Column("degree", sa.String(), nullable=True),
        sa.Column("field_of_study", sa.String(), nullable=True),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_education_user_id", "user_education", ["user_id"])

    # --- Seed reference_job_titles with a real starter set. Honest scope:
    # this is ~110 common titles, not the full O*NET ~57,000 - see
    # app/data/README.md for the full-import follow-up task. Seeding some
    # real data now beats shipping an empty table (which silently returned
    # zero suggestions for every query).
    with open(DATA_DIR / "job_titles_starter.json") as f:
        titles = json.load(f)

    job_titles_table = sa.table(
        "reference_job_titles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("title", sa.String()),
        sa.column("onet_soc_code", sa.String()),
    )
    op.bulk_insert(
        job_titles_table,
        [{"id": uuid.uuid4(), "title": t, "onet_soc_code": None} for t in titles],
    )


def downgrade():
    op.execute("DELETE FROM reference_job_titles")

    op.drop_index("ix_user_education_user_id", table_name="user_education")
    op.drop_table("user_education")

    op.add_column("professional_profiles", sa.Column("school", sa.String(), nullable=True))
    op.add_column("professional_profiles", sa.Column("school_visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("professional_profiles", sa.Column("school_usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("professional_profiles", sa.Column("degree", sa.String(), nullable=True))
    op.add_column("professional_profiles", sa.Column("degree_visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("professional_profiles", sa.Column("degree_usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("professional_profiles", sa.Column("field_of_study", sa.String(), nullable=True))
    op.add_column("professional_profiles", sa.Column("field_of_study_visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("professional_profiles", sa.Column("field_of_study_usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("professional_profiles", sa.Column("graduation_year", sa.Integer(), nullable=True))
    op.add_column("professional_profiles", sa.Column("graduation_year_visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("professional_profiles", sa.Column("graduation_year_usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()))
