# Mingly.ai — Scope & Roadmap

The living plan for Mingly.ai: what the product is, what's built, and the dated path to launch. Updated as decisions are made and milestones ship - status here reflects what's actually live in production, not intent.

**Launch target: January 1, 2027.** _Last updated: October 7, 2026._

---

## What Mingly is

A Cornell startup. A trust-first way for professionals to meet compatible people around the things they already love to do - built on LinkedIn-verified identity, a rich but privacy-controlled profile, and explainable matching. Two ideas shape everything:

- **Activities first.** Insert compatible people into things you already do; shared activities outweigh shared topics.
- **Privacy by default.** Every profile field has two separate controls - *visible on profile* and *usable for matching* - and both are enforced server-side, everywhere.

## Scope

| Pillar | What it covers | Status |
|---|---|---|
| Trusted identity | LinkedIn sign-in; our own copy of the profile photo | ✅ Live |
| Rich, private profile | Professional, education, languages, location + travel radius, pets, interests, activities, lifestyle, About You, photos; per-field privacy | ✅ Live |
| Matching engine | Eligibility (bidirectional preferences, distance, consent), compatibility scoring (activities, interests, career similarity, alumni, languages, pets, lifestyle, goals), friendly explainable intros | ✅ Live |
| Discovery | Ranked feed, Pass / Decide later / Connect, "About them" | ✅ Live |
| Matches & connect | Mutual matching, match moment, Matches page, unmatch, contact info shown only to matches | ✅ Live |
| **Circles & network** | Your Circle = people you trust: **existing friends** (invites, phone contacts) and, later, **people you've met** through Mingly. Secondary network = friends of your circle, as a trust bridge to new people | ✅ Live (lite: invite links, My Circle, friends of friends in matching) |
| **Events & plans** | Local events matched to your interests; interest in the same event as a strong match signal; opt-in sharing with audience controls. Absorbs the original "Activity Engine" | 🆕 Curated pilot pre-beta (NYC + Ithaca); full version post-launch |
| Trust & safety | Report & block (everywhere), admin review, privacy settings, account deletion | ✅ Live |
| Growth | Personal invite links, share sheet, "who's on Mingly" from contacts | Invite links ✅; contacts with the phone apps |
| Monetization | Affiliate ticket links first, sponsored events after scale | 🆕 Post-launch |
| Platforms | Web; iOS and Android (Capacitor wrap of the web app) | Web ✅, phone apps Dec |

---

## Done (live in production)

| Milestone | Completed |
|---|---|
| Foundation: live site, LinkedIn OAuth, Postgres + pgvector, migrations, TLS | Sep 16 |
| Onboarding & profile, privacy model, 2-column design, photos + lightbox | Sep–Oct 1 |
| Matching engine: eligibility, interaction tracking, compatibility scoring | Oct 1–2 |
| Discovery UI with privacy-filtered cards and friendly intros | Oct 3 |
| Matches + Connect: mutual matches, match moment, contact sharing, unmatch | Oct 4 |
| Onboarding matching audit: consent toggles respected everywhere, all 20 fields verified; career similarity, alumni weighting | Oct 4 |
| Core loop fix (people interested in you stay in your feed), Decide later, "About them" | Oct 5 |
| LinkedIn link replaces email in match contact; company in matching by each person's choice | Oct 6 |
| **Circles-lite:** personal invite links carried through sign-in, My Circle page, invite landing page, circle members leave Discovery, friends of friends ranked higher with "You both know Maya" | Oct 7 |
| **Settings & safety:** Settings page (account, privacy overview, mutual-friend setting, blocked people, guidelines, account deletion); report & block from Discover, Matches, and My Circle, enforced in both directions everywhere; suspended and banned accounts locked out; admin review of reports with an audit log | Oct 8 |

Backend: 265 tests. Database at migration 0035.

---

## Path to launch (Oct 6 → Jan 1)

| Dates | Milestone | Exit test |
|---|---|---|
| ✅ **Oct 6–14** | **Circles-lite** (done Oct 7) - personal invite links + share sheet; joining via a link adds you to the inviter's circle (with a confirm step); My Circle page; mutual-friend signal in scoring and intros ("You both know Maya"); "show me as a mutual connection" setting | A friend invited by link joins, lands in the inviter's circle, and a friend-of-friend sees "You both know ..." in Discovery |
| ✅ **Oct 15–23** | **Settings & safety** (done Oct 8, a week early) - Settings page (account deletion button, privacy overview, match contact info, discoverability settings, log out); report & block that remove someone from feed, matches, and circles; simple admin view of reports | Blocking removes a user from every surface in both directions; account deletion works from the UI (an App Store requirement) |
| **Oct 26–30** | **Notifications & backups** - email on new match and on an accepted invite; automated production database + photo backups with a tested restore | A new match triggers an email; a backup is restored to a fresh database successfully |
| **Nov 2–6** | **Phone & legal** - optional verified phone number (needed for contact matching later); "let people find me by my contact info" setting; Terms of Service and Privacy Policy pages (policy updated for invites, phone numbers, and contacts; lawyer review on your side) | Policy and terms live at public URLs; a phone number verifies end to end |
| **Nov 9–13** | **Events pilot (curated, NYC + Ithaca)** - hand-curated events in both pilot cities, mapped to the activity/interest catalog; "Things to do" page; mark interest in an event; see which matches and circle members are interested; event co-interest as a matching signal. Data model includes a `source` field (curated / API / sponsored) so later phases drop in | Two users interested in the same event see it reflected in their match intro |
| Nov 16–20 | Buffer | — |
| **Nov 23–30** | **Web QA & beta prep** (Thanksgiving week) | Full end-to-end pass on desktop and phone browsers: invite → sign up → onboard → discover → match → connect → event |
| **Dec 1–27** | **Private beta (web)** - two cohorts, NYC and Ithaca, recruited through invite links (Cornell networks in both), so each starts with real local density | Real matches and real meetings happen, with feedback captured |
| **Nov 30–Dec 16** (in parallel) | **Phone apps** - Capacitor wrap; contacts permission → "Already on Mingly → add to circle" and "Invite"; store submission and review. Apps join the beta when approved | Approved in both stores |
| **Dec 28–Jan 1** | **Final polish & launch** | — |

**Start now (your side, no code needed):** Apple Developer and Google Play developer accounts - approval can take days to weeks. Also: who's in the beta cohort, and lawyer review of the policy/terms.

---

## After launch

**Q1 2027 - Events & plans v1**
- Automated event sourcing per city (official APIs, venue calendar feeds, city open data - not scraping) with AI categorization into our catalog; research per city, never per user
- Event sharing, decided per event by the person: opt-in, with no pre-selected audience - each share requires choosing from selected people, circle, circle except specific people, circle + friends of friends, or public (with a safety reminder). Separate "interested" and "going"; blocked users never see a share
- Affiliate ticket links - first revenue
- Earned circles: post-meet feedback ("did you meet?") adds people you've met to your circle
- Secondary network surfacing in Discovery, beyond the mutual-friend signal
- Onboarding length revision, informed by beta drop-off data
- Funnel analytics

**Q2 2027 - Smarter matching**
- Semantic embeddings (pgvector) and an ML ranker trained on real behavior, with the heuristic kept as a fallback
- Admin recommendation inspector
- Small-group plans (3–4 people)
- Optional LinkedIn connections spreadsheet import

**H2 2027 - Scale & revenue**
- Sponsored events, with non-negotiables: clear "Sponsored" label, no personal data shared with sponsors (aggregate only), frequency caps, no targeting on sensitive attributes
- Additional cities

---

## Decisions log

- **Contact sharing instead of in-app messaging (V0).** Matches see an optional LinkedIn profile link, phone, and/or Instagram the other person chose to share; nothing is shared by default. Messaging can come later.
- **LinkedIn link instead of email for match contact** - email is too personal for a first reach-out; a LinkedIn profile fits Mingly's professional, trust-first identity. Only genuine linkedin.com/in/ links are accepted.
- **Recurring Routines removed** - revealing real-world patterns ("my gym on Tuesdays") is a safety risk. Event sharing must honor the same lesson.
- **Conversation Topics removed** - redundant with Interests.
- **LinkedIn connections are not available** - LinkedIn closed that data to outside apps in 2015; existing friends come from invites and phone contacts instead.
- **Invites are always sent by the person, from their own device** - Mingly never auto-messages anyone's contacts (spam law; LinkedIn paid $13M over automated contact invitations).
- **Phone contacts never stored for non-users** - matched as fingerprints on the device, non-matches discarded.
- **Same-college alumni is a strong signal regardless of graduation year**; graduation year is intentionally unused.
- **Company counts in matching, by each person's choice** (decided Oct 6) - only when both people allow it via its toggle, so anyone who'd rather not be matched with coworkers can switch it off.
- **Event sharing is fully the person's choice, per event** (decided Oct 6) - nothing is shared automatically and no audience is pre-selected; every share requires picking from all options (selected people, circle, circle except specific people, circle + friends of friends, or public with a safety reminder). Blocked people never see a share.
- **Beta cohort: NYC + Ithaca** (decided Oct 6). Two separate pools that each need their own density; recruited through Cornell networks - on campus in Ithaca, alumni and Cornell Tech in NYC.
- **Pilot cities: New York City and Ithaca, NY** - Mingly is a Cornell startup. The two are ~220 miles apart, so they form separate local pools; people who split time between them (e.g. Cornell Tech in NYC) can list both locations and match in either.
- **"Visible on profile" controls what's shown; "usable for matching" controls what's scored** - a hidden field can count toward matching but is never named or displayed.

## Open decisions


## Risks & contingencies

- **App Store review** can reject a first submission. Contingency: launch on the web January 1 and let the apps follow - the web app is fully functional on phones.
- **Holiday engagement** during a late-December beta - mitigated by starting the web beta December 1.
- **Local density** - matching needs enough people nearby; the beta stays concentrated in the pilot cities and grows through invites. Each city must reach density on its own, since they don't overlap.
- **Capacity** - phone apps run in parallel with the beta; beta fixes take priority, and app work can slip without blocking a web launch.
