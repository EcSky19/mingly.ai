"""professional_profiles and reference_job_titles tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

career_stage_enum = postgresql.ENUM(
    "student", "early_career", "mid_career", "senior", "founder",
    "graduate_student", "career_transition", "other",
    name="careerstage",
)
career_stage_column_type = postgresql.ENUM(
    "student", "early_career", "mid_career", "senior", "founder",
    "graduate_student", "career_transition", "other",
    name="careerstage", create_type=False,
)


def upgrade():
    career_stage_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "professional_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),

        sa.Column("current_role", sa.String(), nullable=True),
        sa.Column("current_role_visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("current_role_usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()),

        sa.Column("company", sa.String(), nullable=True),
        sa.Column("company_visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("company_usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()),

        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("industry_visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("industry_usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()),

        sa.Column("career_stage", career_stage_column_type, nullable=True),
        sa.Column("career_stage_visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("career_stage_usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()),

        sa.Column("school", sa.String(), nullable=True),
        sa.Column("school_visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("school_usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()),

        sa.Column("degree", sa.String(), nullable=True),
        sa.Column("degree_visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("degree_usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()),

        sa.Column("field_of_study", sa.String(), nullable=True),
        sa.Column("field_of_study_visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("field_of_study_usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()),

        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("graduation_year_visible_on_profile", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("graduation_year_usable_for_matching", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_unique_constraint("uq_professional_profiles_user_id", "professional_profiles", ["user_id"])
    op.create_index("ix_professional_profiles_user_id", "professional_profiles", ["user_id"])

    op.create_table(
        "reference_job_titles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("onet_soc_code", sa.String(), nullable=True),
    )
    op.create_index("ix_reference_job_titles_title", "reference_job_titles", ["title"])

    # Enables fast fuzzy/partial matching for job title autocomplete once
    # the table is seeded (see app/data/README.md for seeding status).
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX ix_reference_job_titles_title_trgm ON reference_job_titles "
        "USING gin (title gin_trgm_ops)"
    )


def downgrade():
    op.drop_index("ix_reference_job_titles_title_trgm", table_name="reference_job_titles")
    op.drop_table("reference_job_titles")
    op.drop_table("professional_profiles")
    career_stage_enum.drop(op.get_bind(), checkfirst=True)
