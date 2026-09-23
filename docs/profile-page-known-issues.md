# My Profile page — known issues (flagged, not yet diagnosed)

Flagged after the first real click-through of `/profile` in production. Specifics not yet
gathered — next session should start by walking through the page together to pin down exactly
what's wrong before touching code.

## 1. Photo tagging to activities
Something is off in how a photo's tag (to a loved activity or interest) is working or
displaying. Not yet clear whether this is: the tag not saving correctly, the wrong tag showing,
the tag dropdown not behaving as expected, or something else. Needs a live walkthrough to
reproduce.

## 2. Photo cropping
Uploaded photos aren't cropping/displaying correctly - possibly the grid's `object-fit: cover`
treatment doesn't look right for certain photo aspect ratios, or the resize-on-upload step
(max 1600px, see `app/services/photo_storage.py`) is producing unexpected results. Needs
specific examples of what looks wrong.

## 3. Overall visual design of the Profile page
The page currently reuses the plain onboarding-style CSS (`OnboardingStyles.tsx`) rather than
having its own considered design. This was a deliberate "get it working first" choice for the
first version, but the page likely needs a real design pass - this isn't a form to fill out,
it's meant to be the user's own reference view of themselves.

## Status
None of these are diagnosed yet, let alone fixed. Revisit with a live walkthrough of the actual
page before making changes.
