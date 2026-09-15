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
