# Mingly.ai

**A social community for career-oriented professionals to build their life outside of work.**

Mingly.ai helps professionals meet compatible people for real-world friendships, activities, and social experiences - built on verified identity, a privacy-first profile, and matching that explains itself.

Professionals already have platforms to build their careers. Mingly.ai is being built to help them build the rest of their lives.

A Cornell startup. **Live at [mingly.ai](https://www.mingly.ai)** · Private beta from **December 1, 2026** (New York City and Ithaca, NY) · Launch **January 1, 2027**.

---

## The Problem

Many professionals spend years prioritizing school, careers, and professional growth while their social lives receive less attention - especially after moving to a new city, starting a new job, or graduating.

Existing platforms fall into a few categories: professional networking, dating, large public communities, event listings, and generic friend matching. None are designed around helping career-oriented professionals find people who are genuinely compatible with their lifestyle, background, interests, and the things they actually like to do.

Mingly.ai is designed to fill that gap, around one question:

> **Who would you actually enjoy spending time with, and what could you do together?**

## What Mingly.ai Is Not

- **Not LinkedIn.** LinkedIn is used for trusted sign-in and background signals, but nobody joins Mingly to collect connections or find jobs.
- **Not a dating app.** Relationships may develop naturally, but romantic matching isn't the product.
- **Not an event listing site.** Mingly starts with **people and compatibility**; events are a way for compatible people to make a plan together, not a feed to scroll.

---

## How It Works Today

Everything in this section is live in production.

### 1. Sign in with LinkedIn
Verified professional identity from the start. Mingly keeps its own copy of your profile photo, refreshed each time you sign in.

### 2. Build a profile around your life outside work
Professional background, education, languages, locations with a travel radius, pets, interests, activities, lifestyle, social goals, and photos. Interests and activities can be **liked** or **loved** - loved ones count most.

Every field has **two separate privacy controls**:
- **Visible on profile** - whether other people can see it
- **Usable for matching** - whether it can influence who you're matched with

A field can help your matches without ever being shown. Both controls are enforced on the server, everywhere.

### 3. Matching that explains itself
**Eligibility** comes first: both people's preferences must accept each other (gender and age, in both directions), and you must be within each other's travel radius.

**Compatibility** then ranks everyone eligible, using signals such as:
- shared **activities** (the strongest signal - Mingly is activities-first)
- same **college** - alumni are a strong signal regardless of graduation year
- shared **interests**
- **similar careers** - the same role (ignoring seniority) or the same career field
- shared **languages**, accounting for proficiency
- **pets** - dog people, cat people, and dog compatibility
- **lifestyle**, social goals, and how close you live

Each signal counts only if *both* people allowed it for matching. Instead of a score, each person comes with a short introduction - the way a friend would introduce you:

> *You and Maya both love hiking and running. You're also both into AI and technology. You both went to Cornell and speak Spanish. Plus, you're close by.*

The intro only ever names things the other person made visible.

### 4. Discover
A ranked feed, one person at a time, with their photos, an **About** section, and the activities and interests you can see. Three choices:
- **Connect**
- **Pass**
- **Decide later** - they move to the back of the line and come back later; nothing is lost

### 5. Match and connect
When two people both choose Connect, it's a match. Matches can see each other's optional contact info - a **LinkedIn profile link**, **phone**, and/or **Instagram** - which each person chooses to share, and which nobody else ever sees. Either person can unmatch, which hides contact info immediately.

### 6. Your Circle
Invite friends with a personal link - shared from your own phone, never sent automatically. When they join and accept, you're in each other's circle. Circle members don't appear in Discover (you already know them), but **their friends rank higher**, introduced warmly: *"You and Blake both know Maya."* Anyone can choose not to be named as a mutual friend and still help their friends' matches.

---

## What's Next

The full dated plan lives in **[docs/roadmap.md](docs/roadmap.md)**. In short:

| When | What |
|---|---|
| October | **Settings & safety** - report and block, account deletion (Circles shipped Oct 7) |
| Late Oct–Nov | Match notifications, backups, verified phone numbers, Terms & Privacy Policy, and a **curated events pilot** in NYC and Ithaca |
| December | **Private beta** on the web from Dec 1; **iOS and Android apps**, including finding friends from your phone contacts |
| January 1, 2027 | **Launch** |
| 2027 | Automatically sourced local **events** with audience-controlled sharing, smarter (learned) matching, and sponsored events once the community has grown |

---

## The Mingly Flywheel

```text
Sign in & build a profile
        ↓
Invite your friends → your Circle
        ↓
Discover compatible people (including friends of friends)
        ↓
Match around shared activities and interests
        ↓
Make a plan - an event or activity
        ↓
Meet in real life
        ↓
Grow your Circle → better, more trusted recommendations
```

---

## Product Principles

- **Compatibility over popularity.** Show people the *right* people, not the most popular ones.
- **Real-world interaction over engagement metrics.** A good recommendation gets people off the app and into the world.
- **Career-oriented, not career-focused.** Professional background establishes context and trust; the product is about life outside work.
- **Quality over quantity.** Ten relevant introductions beat hundreds of random profiles.
- **Trust and privacy by design.** Verified identity, separate visibility and matching controls, and nothing shared that a person didn't choose to share.
- **Recommendations should improve.** Every meaningful interaction should make future matching better.

---

## Technology

| Layer | Stack |
|---|---|
| Frontend | Next.js + TypeScript |
| Backend | FastAPI (Python) |
| Database | PostgreSQL + pgvector, migrations with Alembic |
| Auth | Sign In with LinkedIn (OpenID Connect), signed session cookies |
| Infrastructure | Docker Compose, nginx, TLS |

The matching engine lives in `backend/app/services/`: `eligibility.py` (who can be shown), `compatibility_scoring.py` (ranking and the friendly intro), `careers.py` (career similarity), `public_profile.py` (what one person may see about another), and `matches.py` (mutual matches).

### Repository structure

```text
mingly.ai/
├── backend/
│   ├── app/
│   │   ├── api/routes/     # HTTP endpoints
│   │   ├── models/         # database models
│   │   ├── schemas/        # request/response validation
│   │   ├── services/       # matching engine and business logic
│   │   └── data/           # seed catalogs (activities, interests, job titles, ...)
│   ├── alembic/            # database migrations
│   └── tests/
├── frontend/
│   ├── pages/              # onboarding, profile, discover, matches
│   └── components/
├── docs/                   # roadmap, design notes, privacy policy draft
├── infrastructure/
├── docker-compose.yml
└── .env.example
```

---

## Local Development

**Prerequisites:** Docker and Docker Compose, plus a LinkedIn developer app with the **"Sign In with LinkedIn using OpenID Connect"** product.

```bash
git clone https://github.com/EcSky19/mingly.ai.git
cd mingly.ai
cp .env.example .env          # then fill in the values
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

- Web app: http://localhost:3010
- API: http://localhost:8010 (health check at `/api/health`)

Set the LinkedIn redirect URI in both `.env` and your LinkedIn app so they match.

### Tests

```bash
cd backend
pip install -r requirements.txt
SESSION_SECRET=test-secret DATABASE_URL=sqlite:///./test.db pytest
```

The backend suite has 200+ tests, including privacy guarantees (hidden fields never shown or named, opt-outs respected), consent rules for every matching signal, and query-count tests that keep the matching engine from slowing down as the user base grows. Features that depend on PostgreSQL-specific behavior are also verified against a real PostgreSQL database before release.

---

## Documentation

| Doc | What's in it |
|---|---|
| [roadmap.md](docs/roadmap.md) | Scope, what's built, the dated launch plan, decisions log, risks |
| [privacy-policy.md](docs/privacy-policy.md) | Privacy policy draft |
| [location-design.md](docs/location-design.md), [pets-design.md](docs/pets-design.md), [professional-profile-design.md](docs/professional-profile-design.md) | Design notes for profile sections |
| [deployment-log.md](docs/deployment-log.md) | Deployment history |

---

## Security

If you discover a security or privacy vulnerability, please don't open a public GitHub issue. Contact the maintainers privately so it can be investigated responsibly.

## Our Mission

**Help career-oriented professionals build meaningful lives and relationships outside of work.**

People spend years building their careers. **Mingly.ai helps them catch up with life.**

---

**Mingly.ai** · *Meet your kind of people.* · [mingly.ai](https://www.mingly.ai)
