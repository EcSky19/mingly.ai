# Mingly.ai — Build Roadmap

Realistic weekly milestones for taking Mingly.ai from empty repo to internal alpha. Each week ships to the live Hetzner server behind `www.mingly.ai`, gated by invite/access control rather than held back until "done." Assumes steady, near-daily work — if the pace slips, milestones shift, not scope.

Every week ends with: tests passing, a deploy to the server, and this doc updated with actual status (not just intent).

---

## Week 1 — Foundation & Infrastructure ✅ COMPLETE (2026-09-16)

**Status:** exit test passed. `https://www.mingly.ai` is live in production with TLS. LinkedIn login tested end to end with a real account — a real user record exists in the production database. Backend, Postgres+pgvector, and the initial migration are all deployed and verified working. Coming Soon page is live with the real logo.

**Goal:** empty product, but a real one — reachable at `www.mingly.ai`, with auth working end to end.

- Repo structure (frontend / backend / database / docs)
- Hetzner server provisioned: Docker, reverse proxy (Caddy or nginx), TLS for `www.mingly.ai`
- Postgres + `pgvector` running, connected from the backend
- Migrations tooling in place (Alembic)
- LinkedIn OAuth: login, callback, session, logout, re-login
- Bare-bones landing page and "continue with LinkedIn" flow deployed live
- CI: lint, basic tests, build check on every push

**Exit test:** visit `www.mingly.ai` → log in with LinkedIn → land on an empty home screen → log out → log back in. Works in production, not just locally.

---

## Week 2 — Onboarding & User Representation

**Goal:** a user can fully describe themselves and it's stored correctly.

- Professional profile (role, industry, career stage, school)
- Privacy model: `visible_on_profile` vs `usable_for_matching`, enforced server-side
- Location (neighborhood-level, generalized coordinates)
- Interests, activities (top 3 flagged), lifestyle, availability, social cadence, planning style, social comfort, social goals
- Languages, pets, spending preference, conversation interests, recurring routines
- Autosave + resume onboarding

**Exit test:** a new user completes onboarding in ~5 minutes and their structured profile is correctly stored and editable afterward.

---

## Week 3 — Matching Engine V0 (structured + semantic, no ML yet)

**Goal:** real compatibility scoring, not a mock.

- Hard eligibility filtering (location, active account, not blocked, availability overlap)
- Structured compatibility scoring (the weighted heuristic, config-driven, not hardcoded)
- Embedding pipeline for semantic profile (interests, activities, orientation, conversation topics) using `pgvector`
- Semantic similarity as a scoring component
- Truthful, feature-based match explanations (no invented reasons)
- Internal recommendation inspector (admin-only, for debugging scores)

**Exit test:** for any user, generate a ranked top-10 with correct, explainable reasons — verified against hand-picked seed-data cases (strong match, weak match, distance failure, blocked pair).

---

## Week 4 — Activity Engine & Messaging

**Goal:** matches turn into concrete plans, not just profiles to browse.

- Activity candidate generation + ranking for a matched pair/group
- Activity proposal → accept/decline → mutual interest
- Multi-participant plan data model (supports groups from day one, even if UI only shows 1:1 for now)
- Messaging unlocked only through mutual activity interest (no cold DMs)
- Plan lifecycle states (suggested → coordinating → scheduled → completed/cancelled)

**Exit test:** person recommendation → activity suggestion → mutual interest → conversation opens, works without any manual intervention.

---

## Week 5 — Social Graph: Bring-a-Friend, Meetings, Circles

**Goal:** real-world outcomes start feeding the graph.

- Bring-a-Friend flow (invite from existing Circle, explicit accept)
- Post-meet feedback ("did you meet?" / "want to again?") — private
- Circle formation on qualifying mutual positive feedback
- Circle edges with context (which activity, how many times)
- Small-group plan support (3–4 people), feature-flagged

**Exit test:** a real activity between seed-data test users produces a verified mutual Circle relationship end to end.

---

## Week 6 — Network Effects, Trust & Safety

**Goal:** the graph starts working for you, and the platform is safe to open up.

- Circle-of-Circle candidate surfacing with graph features
- Block (removes both users from all discovery/messaging/proposals) and report
- Basic admin dashboard: users, reports, blocks, account status, moderation actions
- Notifications (in-app + email) for the high-value events only
- Analytics instrumented across the full funnel (signup → ... → Circle → repeat)

**Exit test:** a Circle relationship visibly and correctly influences a new recommendation; blocking fully removes a user from every surface.

---

## Week 7 — Internal Alpha

**Goal:** real people, real usage, real signal.

- Invite ~15–30 real users (friends, early adopters in NYC)
- Manually watch the funnel: profile opens, activity interest, mutual interest, meetings, feedback
- Fix what's actually broken, not what seemed risky in theory
- Start accumulating genuine behavioral data (this is the raw material for Week 8–9)

**Exit test:** at least a handful of real meetings happen through the product, with feedback captured.

---

## Week 8 — ML Ranker V0

**Goal:** move from a pure heuristic to a learned ranker, without losing the fallback.

- Feature extraction pipeline (structured + semantic + graph + early behavioral features)
- Bootstrap training labels from the heuristic score (documented as bootstrap, not real preference data)
- Lightweight learning-to-rank model (gradient-boosted, not a custom deep net)
- Model versioning, offline evaluation, heuristic kept as guaranteed fallback
- Recommendation inspector extended to show bootstrap score vs ML score vs final rank

**Exit test:** ML ranker runs in production behind a feature flag, with fallback verified to work if inference fails.

---

## Week 9 — Behavioral Model Update

**Goal:** let real alpha behavior start improving the model.

- Incorporate real acceptance/meeting/feedback/Circle data into retraining
- Compare heuristic baseline vs bootstrap ML vs behaviorally-updated model on actual funnel metrics (not just offline AUC)
- Guard against overfitting on a small dataset (regularization, minimum sample thresholds, baseline blending)

**Exit test:** a documented before/after comparison showing whether behavioral data measurably improved recommendation → meeting conversion.

---

## Week 10 — Closed Beta & Feature Freeze

**Goal:** stop adding scope, start tightening what exists.

- Expand to ~75–150 users, still geographically concentrated in NYC
- Prioritize: onboarding friction, recommendation precision, activity quality, reliability, moderation gaps
- Freeze new matching categories — let real behavior define what comes next
- Full requirements traceability doc up to date, known limitations documented honestly

**Exit test:** the product runs unattended for real users for a week with no manual facilitation required, and you have real data to decide what to build next.

---

## Notes

- This assumes near-daily, focused work. If pace changes, dates shift — not the definition of "done" for each week.
- Every week's exit test must actually pass in production before moving to the next week, not just locally.
- Group support (3–4 people) is built into the data model from Week 4 onward, even before the UI/algorithm fully uses it — avoids a schema rewrite later.
