"""
Reference table for job title autocomplete, sourced from O*NET's public
"Job Titles" dataset. See docs/professional-profile-design.md.

This table is seeded by scripts/import_onet_job_titles.py. The full O*NET
file has ~57,000 rows; see that script's docstring for current import
status (a starter subset ships in this migration's seed data, full import
is a follow-up task - see NOTE in the import script).
"""
import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class JobTitleReference(Base):
    __tablename__ = "reference_job_titles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, index=True)
    onet_soc_code = Column(String, nullable=True)
