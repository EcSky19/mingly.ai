# Location — Field Design

Captures a design decision made before Week 2 implementation: users can have more than one location, free of charge, not gated behind any premium tier.

## Why multi-location

Someone who splits time between two cities for work (consultants, hybrid remote workers, dual-custody arrangements) needs both represented for feasibility matching to work correctly - otherwise the system would wrongly filter them out of matches in a city they're genuinely in on a regular basis.

## Why this is not a premium feature

The original product spec explicitly puts paid subscriptions out of scope for the MVP (see root PRD - "Do not build: ... paid subscriptions"). Beyond that, gating location accuracy behind a paywall would make match quality itself pay-to-win: a free user who genuinely lives between two cities would get systematically worse, less accurate matches than a paying user in the identical situation. That actively undermines the thing the MVP exists to test - whether the platform can produce good real-world connections - and is a bad signal to introduce during an alpha with 25-150 users.

This is different from a feature like Tinder's Passport, which lets a user browse a city they are *not* actually in (vacation planning, remote swiping) - genuine optional exploration, and a reasonable place for a premium feature later if ever wanted. A second *frequently visited* location is closer to basic profile accuracy than a premium convenience.

## Data model

Same pattern as education (see professional-profile-design.md): one-to-many, not a flat second column bolted onto a single-location row.

`user_locations` (already sketched in the root PRD, revised here to be explicitly one-to-many):

```
user_locations
--------------
id
user_id
city
metro
neighborhood
latitude / longitude (generalized, not exact address)
travel_radius
transport_preferences
is_primary (boolean - exactly one location per user should be true)
label (optional, e.g. "Work" / "Home" - free text, user's own words)
```

## Behavior

- A user can add a second (or more) location during onboarding or later from settings - not required, default is one location.
- Exactly one location is marked `is_primary`. This drives default discovery/matching unless a specific plan or context calls for the secondary location.
- Feasibility scoring (see root PRD's hard eligibility filtering) should check distance/availability against *any* of a user's locations that overlaps with the candidate's, not just the primary one - otherwise the whole point of adding a second location is defeated.
- Recommendation explanations (see root PRD's truthful, feature-based reason codes) should be able to say something like "both spend time in Brooklyn" even if that's a secondary location for one person, so the match makes sense to the user rather than looking arbitrary.

## Implementation note for Week 2

Build `user_locations` as multi-row from day one - do not build a single-row version now and migrate later, the way education had to be redesigned after initial feedback. Location is explicitly called out in this doc precisely to avoid repeating that rework.

## City and neighborhood autocomplete

Added after initial build shipped with plain free-text city/neighborhood fields - real user feedback flagged the missing autocomplete.

**Provider:** Photon (by Komoot), an OpenStreetMap-based geocoder explicitly built for search-as-you-type. **Not Nominatim** - Nominatim's own usage policy explicitly forbids autocomplete use ("Auto-complete search... you must not implement such a service"), and Photon's README specifically points Nominatim users here for exactly this use case. Free, no API key, welcomes reasonable end-user-triggered volume per its usage policy - request headers identify the app with a proper User-Agent, per that policy.

**City field:** queries Photon filtered to `layer=city` and `layer=locality` (catches smaller towns not tagged strictly as cities). Returns name, state/country as subtitle, and latitude/longitude - the coordinates are captured and stored (not just the display name), since they enable location-biased neighborhood search and, later, real distance-based feasibility matching (see root PRD's location model).

**Neighborhood field:** queries Photon filtered to `layer=district` and `layer=locality`, biased toward the selected city's coordinates (via Photon's `lat`/`lon`/`location_bias_scale` params) so searching "Park Slope" after selecting New York doesn't surface a same-named place elsewhere. Disabled until a city is selected, since the bias needs city coordinates to be meaningful - the field shows a "enter a city first" hint rather than silently ignoring the dependency.

**Fails open the same way as every other autocomplete field** - if Photon is unreachable or returns nothing, city and neighborhood both remain plain free text.
