# Professional Profile — Field Design

Captures a design decision made before Week 2 implementation: every professional-context field in onboarding is independently optional, and the company field specifically has an industry-only fallback for users who don't want to name their employer.

## Why

LinkedIn login only provides identity (name, email, photo) — not job title, company, or education (see `docs/deployment-log.md` for why: LinkedIn's Profile API requires partner approval we don't have and likely wouldn't get for a consumer app). All professional context is typed in by the user during onboarding, which means we control exactly how much pressure to put on them to share it. Given the product's own principle ("identity, not status" — see README), the honest default is to make all of it skippable, and to give a lower-disclosure option for the field most likely to feel exposing: the specific employer name.

## Field behavior

| Field | Required? | Notes |
|---|---|---|
| `current_role` | Optional | Free text or skip |
| `company` | Optional | If skipped, user can instead select `industry` alone as a lower-disclosure substitute |
| `industry` | Optional | Standalone field, or serves as the fallback when `company` is skipped |
| `career_stage` | Optional | Enum (e.g. early-career, mid-career, graduate student, founder) |
| `school` | Optional | Free text or skip |
| `degree` / `field_of_study` | Optional | Free text or skip |
| `graduation_year` | Optional | |

Every field above additionally carries the existing privacy toggle pair from the PRD:
- `visible_on_profile`: shown to other users
- `usable_for_matching`: used in the recommendation pipeline

These are independent — a user can, for example, share `industry` for matching purposes only, with `visible_on_profile = false`, while sharing nothing else about their professional life publicly.

## Implementation note for Week 2

The `professional_profiles` table (see roadmap Week 2) should make every column above nullable, with the privacy flags stored per-field (or per-field-group if that proves simpler once the onboarding UI is built) rather than one blanket privacy setting for the whole professional section. The onboarding UI should present company/industry as a single UI step with two paths ("share company" vs "just share industry"), not as two separate unrelated form fields, so the intent is clear to the user.

## Company name autocomplete

As the user types in the `company` field, suggest real company names for a better typing experience (avoids typos, normalizes names like "Google" vs "Google LLC" vs "google.com").

**Provider:** Clearbit's Company Autocomplete API (`https://autocomplete.clearbit.com/v1/companies/suggest?query=...`). Free, no registration/API key required as of 2026 (confirmed still free after Clearbit sunset most of their other free tools in April 2025). Returns `[{name, domain, logo}, ...]`.

**Architecture:** proxy through our own backend rather than calling Clearbit directly from the browser:
- New endpoint: `GET /api/companies/autocomplete?q=<partial>`
- Backend calls Clearbit server-side, returns just `{name, domain}` pairs (drop the logo - we don't need it)
- Debounce on the frontend (e.g. 250ms) before firing a request, don't fire on every keystroke
- If the Clearbit call fails or times out, fail open - the field remains a normal free-text input, never blocks the user from typing and submitting a company name that isn't in Clearbit's index (many real companies, especially small/early-stage ones, won't be)

This keeps us able to swap providers later (e.g. if Clearbit changes its free-tier terms) without any frontend changes, and keeps company names optional/free-text underneath the suggestions - autocomplete is a UX aid, never a validation gate.

## School name autocomplete

Same pattern, applied to the `school` field.

**Provider:** Hipolabs Universities API (`http://universities.hipolabs.com/search?name=<partial>`). Free, no API key, no registration. Covers roughly 10,000+ institutions worldwide, searchable by name and/or country. Returns `[{name, country, domain, web_page}, ...]`.

**Architecture:** same as company autocomplete -
- New endpoint: `GET /api/schools/autocomplete?q=<partial>`
- Backend proxies to Hipolabs server-side, returns just `{name, country}` pairs
- Debounced on the frontend, same as company
- **Explicit "my school isn't listed" fallback:** the suggestion dropdown always includes a final option like "Can't find your school? Enter it manually" - clicking it (or simply not selecting any suggestion and just typing/submitting) switches the field to plain free text. This matters because Hipolabs' list, while large, won't include every trade school, bootcamp, small international institution, or program someone might have attended - the fallback is not an edge case, it's a first-class path, same as company.
- Same fail-open behavior if the Hipolabs call errors or times out: field remains usable as free text.

## Degree and field of study autocomplete

Different approach from company/school, deliberately. Company names and school names are huge, open-ended, constantly-changing universes (millions of companies; schools open/close/rename) - that's why those need live third-party APIs. Degree types and fields of study are the opposite: **bounded, stable, well-known lists**. Depending on another external API for these would add a third-party failure point for no real benefit. Both ship as static lists bundled directly in our own app - no external API call, no rate limits, works offline, nothing to fail open from.

**Degree type** (`degree` field): a short curated list we own and maintain ourselves (~20-30 entries) - Associate's (AA/AS), Bachelor's (BA/BS/BFA/BEng), Master's (MA/MS/MBA/MEd/MFA/LLM), Doctoral (PhD/EdD/JD/MD/DO/PsyD), Professional Certificate, and an explicit "Other" / free-text option. No external dataset needed; this list is small and slow-changing enough to hand-maintain in the codebase.

**Field of study** (`field_of_study` field): sourced from the U.S. Department of Education's **CIP (Classification of Instructional Programs)** codes - the standard federal taxonomy of academic fields, public domain, free, and stable (used by NCES and referenced by universities' own registrars). We'll use the CIP 2020 4-digit level (~400 categories - "Computer Science," "Economics," "Mechanical Engineering") rather than the full 6-digit level (2,000+ narrow subcategories), since 4-digit is granular enough to be useful without overwhelming the autocomplete with near-duplicate entries. Bundled as a static JSON file in the repo (e.g. `backend/app/data/cip_fields_of_study.json`), not fetched from any live API.

Both fields keep the same UX pattern as company/school: type-ahead search against the bundled list, with a "not listed / enter manually" free-text fallback always available, since not everyone's actual field of study or credential type will cleanly match a fixed taxonomy.
