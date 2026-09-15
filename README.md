# Mingly.ai

A LinkedIn-gated, ML-first social platform for career-oriented professionals — built to help people build a life *outside* of work.

Mingly.ai is **not** professional networking, recruiting, or dating. It's a social community that uses machine learning to recommend compatible people (and small groups) and concrete, low-pressure activities to do together, then learns from what actually happens in the real world to get better over time.

## The Core Loop

```
LinkedIn-required signup
        ↓
Rich onboarding (professional context, lifestyle, interests, activities,
availability, language, social style, routines, pet preferences)
        ↓
Structured + semantic user representation
        ↓
Hard eligibility / safety / privacy filtering
        ↓
Hybrid ML compatibility ranking (bootstrap heuristic + learning-to-rank)
        ↓
Recommend compatible people — 1:1 or small groups (up to ~4)
        ↓
Recommend a concrete activity for that group to do together
        ↓
Accept / coordinate, with optional Bring-a-Friend
        ↓
Real-world meeting
        ↓
Private post-meet feedback (did you meet? want to again?)
        ↓
Mutually positive outcomes become a contextual Circle relationship
        ↓
Circle-of-Circle discovery expands the trusted graph
        ↓
Behavioral outcomes feed back into the ranking model
        ↓
Every successful connection makes future recommendations better
```

## What Makes This Different

- **Identity, not status.** LinkedIn is required at signup purely for identity/trust context — never as a prestige ladder. Recommendations never rank people by salary, employer prestige, or school prestige.
- **Group-aware from the start.** The recommendation unit is a *compatible set of people* (1 to ~4), not just a pair. Small-group matching, Bring-a-Friend, and group activity plans are core to the data model, not a later add-on.
- **Two-sided matching.** The system recommends both *who* to meet and *what to actually do together*, drawing heavily on each user's stated top activities and existing routines — inserting compatible people into things users already do rather than asking them to invent new plans.
- **Hybrid ML, not a black box.** Hard safety/privacy/feasibility rules always outrank the model. Structured features and semantic embeddings feed a bootstrap heuristic score, blended with a learning-to-rank model as real behavioral data accumulates. Explanations shown to users are generated from real ranking features — never invented by an LLM.
- **Real-world outcomes as ground truth.** The product explicitly asks whether people actually met and whether they'd want to again. That signal — not clicks or engagement — is what the model optimizes toward.
- **Circles, not connection requests.** A Circle relationship only forms after a real interaction produced mutual positive feedback. Circle edges carry context (which activity, how many times), and Circle-of-Circle discovery uses that context to surface new, more trustworthy recommendations.
- **The moat is behavioral.** Profile data (school, job, interests) is replicable. Who was recommended to whom, who met, what worked, and which relationships became Circles is not — that behavioral + contextual graph is the long-term differentiator, and the architecture is designed to preserve it from day one.

## Explicitly Out of Scope

No public feed, no swiping/dating mode, no romantic-preference filters, no recruiting or referral tooling, no platform-hosted events, no native mobile apps in the MVP, and no enterprise-scale ML infrastructure (no separate vector DB cluster, no custom deep ranking architecture, no online real-time learning) until real usage demonstrates the need.

## Status

Early build. See `/docs` for architecture, database schema, ML system design, and requirements traceability as they're written.

## Tech Stack (planned)

- **Frontend:** Next.js, React, TypeScript — mobile-first responsive web (PWA-capable)
- **Backend:** Python, FastAPI, modular monolith
- **Database:** PostgreSQL + SQLAlchemy + Alembic, with `pgvector` for semantic embeddings
- **ML:** interpretable learning-to-rank model (e.g. gradient-boosted ranker) layered on structured + semantic + graph + behavioral features, with a heuristic fallback always available

## Contributing

Private repo, early-stage. Not yet accepting external contributions.
