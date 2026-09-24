# My Profile page — known issues

## 1. Photo tagging flow — RESOLVED
Was: tag chosen before file selection, upload happened automatically on file select, no
explicit "don't tag this" option.
Fixed: photo is selected first, then a preview + tag dropdown (with an explicit "Prefer not to
tag" option) appears, then an explicit "Upload photo" button confirms. A "Cancel" option
discards the pending selection. See commit `1252788`.

## 2. Photo cropping — RESOLVED
Was: `object-fit: cover` on the photo grid was cropping non-square photos to fill a square
frame - backend resizing was always correct (`.thumbnail()` preserves aspect ratio and never
crops), this was purely a frontend display bug.
Fixed: `object-fit: contain` with a background fill, so the full image always shows. See
commit `acb4c02`.

## 3. Overall visual design of the Profile page — STILL OPEN
The page still reuses the plain onboarding-style CSS (`OnboardingStyles.tsx`) rather than
having its own considered design. Today's fixes addressed specific functional/UX bugs (the
tagging flow, the ugly native file input, the cropping bug) but not a real design pass for the
page as a whole. This isn't a form to fill out - it's meant to be the user's own reference view
of themselves, and the visual treatment should probably reflect that.

## Status
2 of the original 3 flagged issues are fixed and deployed. The visual design pass is still
open - revisit when ready to think through what this page should actually look and feel like,
not just function correctly.
