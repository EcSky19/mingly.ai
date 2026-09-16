# Pets — Field Design

Captures a design decision made before Week 2/3 implementation: pets are a matching and activity-recommendation dimension, not just a profile field to fill in and forget.

## Why this needs its own doc

It would be easy to build pets as a single onboarding checkbox ("do you have a dog?") and stop there. That undersells what the root PRD already calls for: pet compatibility combining human compatibility + activity compatibility + pet feasibility, and a "Bring a Pet" concept in the activity plan itself (see root PRD sections 31 and 52). This doc makes that connection explicit so Week 2 (onboarding) and Week 3 (matching engine) build compatible pieces instead of pets being a dead-end profile field that never reaches the recommendation system.

## Week 2 — Onboarding

**Pet profile** (per user, optional):
- Type: dog / cat / other
- For dogs specifically: name, size, activity level, comfortable with other dogs
- Non-owners: a simple "comfortable with dogs" flag, so they aren't excluded from dog-adjacent matches just for not owning one themselves

**Pet-related activity interests** - not a separate bolted-on field, but entries in the *same* activity-interest data structure every other activity uses (see root PRD section 19-22, and the activities vs. interests distinction already established): dog walks, dog parks, dog-friendly cafes, hiking with dogs, running with dogs, meeting other dog owners. A user who loves dog-related activities but doesn't own one yet (e.g. wants to meet people through walking their friend's dog, or is considering getting one) can still select these.

## Week 3 — Matching engine

Pet compatibility is a real feature group in the structured compatibility score (see root PRD section 40, "Pets" under feature generation), combining:
- Pet ownership match (both have dogs, one has/one is comfortable, etc.)
- Dog-to-dog compatibility where relevant (size, activity level, sociability)
- Shared pet-related activity interest (independent of ownership - someone without a dog who loves dog parks is still a relevant signal)

**Activity ranking must be pet-aware**, not just people-matching. When the system generates a suggested activity for a compatible pair/group, it should be able to propose "dog walk Thursday evening" the same way the root PRD's example shows, factoring in both people's actual pets and stated preferences - not just whether they both like the idea of dogs in the abstract. This means the activity engine (Week 4 per the roadmap) needs "bring your dog" as a first-class option on an activity plan, matching the root PRD's Bring-a-Pet concept - visible in the plan itself, not a hidden profile attribute nobody sees again after onboarding.

## Implementation note

Do not build pets as an isolated onboarding-only feature. The onboarding data model (pet profile + pet activity interests) and the matching/activity engine (Week 3-4) should be designed together from the start, using the same activity-interest structures already planned for non-pet activities, so pets flow through the whole loop: profile → match → suggested activity → real-world meeting - exactly like every other interest/activity, rather than a special case.
