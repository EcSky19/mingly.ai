# Backend Data Files

## `degrees.json`
Curated list of ~34 common degree types. Hand-maintained, not sourced from an external dataset (see `docs/professional-profile-design.md` for why - this list is small and stable enough not to need one). Considered essentially complete for MVP purposes; expand as real users report missing options via the "Other" free-text fallback.

## `fields_of_study_starter.json`
**Honest status: this is a starter subset (75 common fields), not the full CIP taxonomy** the design doc originally called for (~2,000 entries at the 6-digit level). The full CIP dataset exists as public federal/Statistics-Canada data, but pulling and parsing the actual file requires network access this environment didn't have during initial build (the source file is a binary CSV on statcan.gc.ca, outside the sandbox's network allowlist).

**Follow-up task:** replace this file with a real import of the full CIP 2020 dataset. Options, in order of preference:
1. Download the official NCES CIP 2020 text/CSV export directly (nces.ed.gov/ipeds/cipcode) from a machine with unrestricted network access, then commit the resulting JSON to this repo
2. Use the Statistics Canada CIP 2021 CSV mirror referenced in `docs/professional-profile-design.md`
3. In the meantime, the free-text fallback (see design doc) means no real user is blocked by this gap - they just won't get a suggestion for less common fields of study until the import happens

## `../models/job_title.py` (`reference_job_titles` table)
Not yet seeded. See `scripts/import_onet_job_titles.py` (to be written) for the planned O*NET import. Until that exists, the `/api/job-titles/autocomplete` endpoint should be built to handle an empty table gracefully (falls through to free text every time), not assume data is present.
