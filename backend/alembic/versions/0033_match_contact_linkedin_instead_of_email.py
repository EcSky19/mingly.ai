"""match contacts: LinkedIn profile link instead of email

Revision ID: 0033
Revises: 0032
Create Date: 2026-10-05

Email was removed as too personal for a first reach-out; a LinkedIn profile
link fits Mingly's professional, trust-first identity better. Any emails
already saved are deliberately discarded - we stop holding data we decided
not to collect.
"""
from alembic import op
import sqlalchemy as sa

revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user_match_contacts", sa.Column("linkedin_url", sa.String(), nullable=True))
    op.drop_column("user_match_contacts", "email")


def downgrade():
    # The discarded emails can't be restored; this only restores the column.
    op.add_column("user_match_contacts", sa.Column("email", sa.String(), nullable=True))
    op.drop_column("user_match_contacts", "linkedin_url")
