# Onboarding Length — Known Concern, Deferred Decision

Logged 2026-09-21. Not an action item right now - a real product decision to revisit once the "My Profile" page exists.

## The problem

The root PRD (section 36) targets onboarding at **4-6 minutes maximum**. As built, onboarding is currently 6 pages:

1. `/onboarding` - personal/professional info, education (multi-entry), languages (multi-entry), location (multi-entry), pets (multi-entry)
2. `/onboarding/interests` - interests, conversation topics, activities
3. `/onboarding/activity-details` - per-loved-activity detail (conditional)
4. `/onboarding/social` - lifestyle, career orientation, social preferences, spending, city/circle status

Each page has multiple fields, several of them multi-entry sections. Realistically this is well past the original 4-6 minute target, even though every individual field is optional and skippable.

## The direction being considered (not decided yet)

Once the "My Profile" page exists (see docs/roadmap.md), some fields currently in mandatory onboarding could move to being **editable primarily via the Profile page** instead - i.e., a new user completes a shorter, faster initial onboarding to get into the app quickly, then enriches their profile over time via Profile page edits rather than facing everything up front.

This is a known pattern (progressive profiling) and would directly address the "too long" concern without losing any of the data model or fields we've already built - it's purely a question of *when* a user is asked to fill something in, not *whether* the field exists.

## What needs to happen before deciding

1. Build the "My Profile" page first (in progress - see current chat/roadmap)
2. Once it exists, revisit which fields genuinely need to be in the first-run flow (e.g., enough to make Week 3's matching engine useful) versus which can be deferred to "fill in later, from your profile"
3. This is explicitly *not* being decided or built right now - noted so it doesn't get lost, not as a task to execute yet
