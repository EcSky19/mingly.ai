// Shared dark-theme styles for all onboarding pages (personal info,
// interests & activities, and any future steps). Extracted from the
// original single onboarding page so multiple pages can share one
// visual identity without duplicating ~300 lines of CSS.
export default function OnboardingStyles() {
  return (
    <style>{`
      * { box-sizing: border-box; }
      html, body { margin: 0; padding: 0; background: #1b1730; }

      .page {
        min-height: 100vh;
        background: radial-gradient(120% 140% at 100% 0%, #241f3d 0%, #1b1730 55%), #1b1730;
        font-family: "Public Sans", sans-serif;
        color: #f6f1e7;
        padding: 4vh 6vw 5vh;
      }

      .loading { color: #b9afd1; font-family: "Public Sans", sans-serif; padding: 4vh 6vw; }

      .wrap { max-width: 560px; margin: 0 auto; }

      .wordmark {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
      }
      .mark { height: 1.4rem; width: auto; }
      .wordmark span:last-child {
        font-family: "Fraunces", serif;
        font-size: 0.95rem;
        font-weight: 500;
        color: #e8a548;
      }

      .headline {
        font-family: "Fraunces", serif;
        font-weight: 600;
        font-size: clamp(1.5rem, 3.4vw, 2.15rem);
        line-height: 1.1;
        margin: 0 0 0.75rem 0;
        white-space: nowrap;
      }

      .subhead {
        color: #b9afd1;
        line-height: 1.6;
        max-width: 42em;
        margin: 0 0 1.75rem 0;
      }

      .section {
        margin-bottom: 1.5rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid rgba(185, 175, 209, 0.15);
      }
      .section:last-of-type { border-bottom: none; }

      .section-header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-bottom: 0.5rem;
      }

      .section-title {
        font-family: "Fraunces", serif;
        font-weight: 500;
        font-size: 1.15rem;
        margin: 0 0 0.85rem 0;
        color: #f6f1e7;
      }
      .section-header-row .section-title { margin-bottom: 0; }

      .toggle-pair {
        display: flex;
        gap: 0.5rem;
      }
      .toggle-btn {
        background: transparent;
        border: 1px solid rgba(185, 175, 209, 0.35);
        color: #b9afd1;
        font-family: "Public Sans", sans-serif;
        font-size: 0.85rem;
        padding: 0.4rem 0.8rem;
        border-radius: 4px;
        cursor: pointer;
      }
      .toggle-btn.active {
        background: rgba(232, 165, 72, 0.15);
        border-color: #e8a548;
        color: #e8a548;
      }

      .field {
        position: relative;
        margin-bottom: 0.6rem;
      }
      .field-label {
        display: block;
        font-size: 0.85rem;
        color: #b9afd1;
        margin-bottom: 0.4rem;
      }
      .field-input {
        width: 100%;
        background: #2c2650;
        border: 1px solid rgba(185, 175, 209, 0.25);
        color: #f6f1e7;
        font-family: "Public Sans", sans-serif;
        font-size: 1rem;
        padding: 0.7rem 0.85rem;
        border-radius: 4px;
      }
      .field-input:focus {
        outline: none;
        border-color: #e8a548;
      }
      .field-input:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      select.field-input {
        appearance: none;
      }

      .suggestions {
        position: absolute;
        top: calc(100% + 4px);
        left: 0;
        right: 0;
        background: #2c2650;
        border: 1px solid rgba(185, 175, 209, 0.3);
        border-radius: 4px;
        max-height: 220px;
        overflow-y: auto;
        z-index: 10;
      }
      .suggestion {
        display: flex;
        justify-content: space-between;
        width: 100%;
        background: transparent;
        border: none;
        color: #f6f1e7;
        font-family: "Public Sans", sans-serif;
        font-size: 0.95rem;
        text-align: left;
        padding: 0.6rem 0.85rem;
        cursor: pointer;
      }
      .suggestion:hover { background: rgba(232, 165, 72, 0.12); }
      .suggestion-subtitle { color: #8f84ad; font-size: 0.85rem; }
      .suggestion-hint {
        color: #8f84ad;
        font-size: 0.85rem;
        padding: 0.6rem 0.85rem;
      }

      .privacy-row {
        display: flex;
        gap: 1.25rem;
        margin: 0.4rem 0 1.5rem 0;
      }
      .privacy-toggle {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.8rem;
        color: #8f84ad;
      }
      .privacy-toggle input { accent-color: #e8a548; }

      .education-entry {
        margin-bottom: 1.25rem;
        padding-bottom: 1.25rem;
        border-bottom: 1px dashed rgba(185, 175, 209, 0.2);
      }
      .education-entry:last-of-type { border-bottom: none; }

      .education-entry-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
      }
      .education-entry-label {
        font-size: 0.8rem;
        color: #8f84ad;
        text-transform: none;
      }
      .remove-entry {
        background: transparent;
        border: none;
        color: #b9afd1;
        font-size: 0.8rem;
        cursor: pointer;
        text-decoration: underline;
      }

      .add-entry {
        background: transparent;
        border: 1px dashed rgba(185, 175, 209, 0.35);
        color: #b9afd1;
        font-family: "Public Sans", sans-serif;
        font-size: 0.9rem;
        padding: 0.6rem 1rem;
        border-radius: 4px;
        cursor: pointer;
        width: 100%;
        text-align: center;
      }
      .add-entry:hover {
        border-color: #e8a548;
        color: #e8a548;
      }

      .section-hint {
        font-size: 0.85rem;
        color: #8f84ad;
        margin: 0 0 1rem 0;
        line-height: 1.5;
      }

      .set-primary {
        background: transparent;
        border: none;
        color: #e8a548;
        font-size: 0.8rem;
        cursor: pointer;
        text-decoration: underline;
        padding: 0;
        margin-top: -0.4rem;
      }

      .chip-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
      }

      .other-entry-row {
        display: flex;
        gap: 0.6rem;
        margin-top: 1rem;
      }
      .other-entry-row .field-input {
        flex: 1;
      }
      .other-add-btn {
        width: auto;
        padding: 0.7rem 1.25rem;
        white-space: nowrap;
      }
      .other-add-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .chip {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        background: #2c2650;
        border: 1px solid rgba(185, 175, 209, 0.25);
        color: #b9afd1;
        font-family: "Public Sans", sans-serif;
        font-size: 0.9rem;
        padding: 0.5rem 0.9rem;
        border-radius: 999px;
        cursor: pointer;
        transition: background 120ms ease, border-color 120ms ease, color 120ms ease;
      }

      .chip-liked {
        background: rgba(74, 222, 128, 0.15);
        border-color: #4ade80;
        color: #f6f1e7;
      }

      .chip-loved {
        background: rgba(244, 114, 182, 0.15);
        border-color: #f472b6;
        color: #f6f1e7;
      }

      .chip-heart {
        color: #f472b6;
        font-size: 0.85rem;
      }

      .chip-check {
        color: #4ade80;
        font-size: 0.8rem;
      }

      .top-activity-context {
        margin-top: 1.75rem;
      }

      .actions {
        display: flex;
        align-items: center;
        gap: 1.5rem;
        margin-top: 1rem;
      }
      .cta {
        background: #e8a548;
        color: #1b1730;
        font-weight: 600;
        font-size: 1rem;
        border: none;
        padding: 0.85rem 1.75rem;
        border-radius: 4px;
        cursor: pointer;
      }
      .cta:disabled { opacity: 0.6; cursor: default; }
      .skip {
        background: transparent;
        border: none;
        color: #b9afd1;
        font-size: 0.9rem;
        cursor: pointer;
        text-decoration: underline;
      }
      .back-link {
        background: transparent;
        border: none;
        color: #8f84ad;
        font-size: 0.85rem;
        cursor: pointer;
        text-decoration: underline;
        padding: 0;
        margin-bottom: 2rem;
      }
      .saved-hint { color: #8f84ad; font-size: 0.85rem; margin-top: 1rem; }

      .profile-linkedin-photo {
        width: 96px;
        height: 96px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid rgba(232, 165, 72, 0.4);
      }

      .photo-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 1rem;
        align-items: start;
      }
      .photo-slot {
        position: relative;
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
      }
      .photo-thumb {
        width: 100%;
        height: auto;
        display: block;
        border-radius: 8px;
        border: 1px solid rgba(185, 175, 209, 0.25);
      }
      .photo-tag-label {
        font-size: 0.8rem;
        color: #e8a548;
      }
      .photo-remove-btn {
        background: transparent;
        border: none;
        color: #b9afd1;
        font-size: 0.8rem;
        cursor: pointer;
        text-decoration: underline;
        text-align: left;
        padding: 0;
      }

      .pending-photo-upload {
        margin-top: 1.25rem;
        padding: 1.25rem;
        border: 1px dashed rgba(185, 175, 209, 0.3);
        border-radius: 8px;
      }
      .pending-photo-upload .photo-thumb {
        max-width: 220px;
        margin-bottom: 1rem;
      }
      .pending-photo-upload .actions {
        margin-top: 1rem;
      }

      .privacy-tag {
        display: inline-block;
        font-size: 0.75rem;
        color: #8f84ad;
        margin-left: 0.5rem;
      }

      .profile-item {
        margin-bottom: 0.75rem;
        line-height: 1.5;
      }
      .profile-item-label {
        color: #b9afd1;
        font-size: 0.85rem;
      }
      .profile-empty-hint {
        color: #8f84ad;
        font-size: 0.85rem;
        font-style: italic;
      }
      .edit-link {
        background: transparent;
        border: none;
        color: #e8a548;
        font-size: 0.85rem;
        cursor: pointer;
        text-decoration: underline;
        padding: 0;
      }
      .profile-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.5rem;
      }
      .profile-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(74, 222, 128, 0.15);
        border: 1px solid #4ade80;
        color: #f6f1e7;
        font-size: 0.85rem;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
      }
      .profile-chip-loved {
        background: rgba(244, 114, 182, 0.15);
        border-color: #f472b6;
      }
      .profile-chip-icon-check {
        color: #4ade80;
        font-size: 0.8rem;
      }
      .profile-chip-icon-heart {
        color: #f472b6;
        font-size: 0.8rem;
      }

      .collapsible-header-static { cursor: default; }
      .collapsible-section {
        margin-bottom: 0;
        padding-bottom: 0;
        border-bottom: none;
      }
      .collapsible-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        background: transparent;
        border: none;
        padding: 1rem 0;
        margin: 0;
        cursor: pointer;
        text-align: left;
        border-bottom: 1px solid rgba(185, 175, 209, 0.15);
      }
      .collapsible-header .section-title {
        margin: 0;
      }
      .collapsible-header-right {
        display: flex;
        align-items: center;
        gap: 0.6rem;
      }
      .collapsible-summary {
        color: #8f84ad;
        font-size: 0.85rem;
      }
      .collapsible-chevron {
        color: #8f84ad;
        font-size: 0.9rem;
        transition: transform 150ms ease;
      }
      .collapsible-chevron-open {
        transform: rotate(180deg);
      }
      .collapsible-body {
        padding-top: 1.25rem;
        padding-bottom: 0.5rem;
      }
      .collapsible-body:last-child {
        padding-bottom: 0;
      }

      .radius-slider {
        width: 100%;
        -webkit-appearance: none;
        appearance: none;
        height: 4px;
        border-radius: 2px;
        background: rgba(185, 175, 209, 0.25);
        outline: none;
        margin: 0.5rem 0 1rem 0;
      }
      .radius-slider::-webkit-slider-thumb {
        -webkit-appearance: none;
        appearance: none;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: #e8a548;
        cursor: pointer;
        border: 2px solid #1b1730;
      }
      .radius-slider::-moz-range-thumb {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: #e8a548;
        cursor: pointer;
        border: 2px solid #1b1730;
      }
      .radius-slider::-moz-range-track {
        height: 4px;
        border-radius: 2px;
        background: rgba(185, 175, 209, 0.25);
      }

      /* Profile page 2-column layout only - .wrap stays untouched since
         it's shared with the single-column onboarding forms. */
      .profile-wrap { max-width: 960px; margin: 0 auto; }
      .profile-columns {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0 3rem;
        align-items: start;
      }
      @media (max-width: 860px) {
        .profile-columns {
          grid-template-columns: 1fr;
        }
      }

      .lightbox-overlay {
        position: fixed;
        inset: 0;
        background: rgba(10, 8, 20, 0.92);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
      }
      .lightbox-image {
        max-width: 90vw;
        max-height: 90vh;
        object-fit: contain;
        border-radius: 4px;
      }
      .lightbox-close {
        position: fixed;
        top: 1.25rem;
        left: 1.25rem;
        background: rgba(246, 241, 231, 0.12);
        border: none;
        color: #f6f1e7;
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 50%;
        font-size: 1.1rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 150ms ease;
      }
      .lightbox-close:hover {
        background: rgba(246, 241, 231, 0.22);
      }
      .lightbox-arrow {
        position: fixed;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(246, 241, 231, 0.12);
        border: none;
        color: #f6f1e7;
        width: 3rem;
        height: 3rem;
        border-radius: 50%;
        font-size: 1.75rem;
        line-height: 1;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 150ms ease;
      }
      .lightbox-arrow:hover {
        background: rgba(246, 241, 231, 0.22);
      }
      .lightbox-arrow-left { left: 1.25rem; }
      .lightbox-arrow-right { right: 1.25rem; }

      /* Discovery (/home) */
      .discover-topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
      }
      .discover-topbar .wordmark { margin-bottom: 0; }
      .discover-nav {
        display: flex;
        gap: 1.25rem;
        align-items: center;
      }
      .discover-nav-link {
        background: transparent;
        border: none;
        color: #b9afd1;
        font-size: 0.9rem;
        cursor: pointer;
        padding: 0;
      }
      .discover-nav-link:hover { color: #f6f1e7; }
      .discover-nav-link-active {
        color: #e8a548;
        font-weight: 600;
      }

      /* Matches (/matches) */
      .matches-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.25rem;
        align-items: start;
      }
      @media (max-width: 860px) {
        .matches-grid { grid-template-columns: 1fr; }
      }
      .match-card {
        background: #241f3d;
        border: 1px solid rgba(185, 175, 209, 0.2);
        border-radius: 12px;
        padding: 1.25rem;
      }
      .match-header {
        display: flex;
        align-items: center;
        gap: 1rem;
      }
      .match-avatar {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid rgba(232, 165, 72, 0.4);
        flex-shrink: 0;
      }
      .match-avatar-placeholder {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: #2c2650;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: "Fraunces", serif;
        font-size: 1.6rem;
        color: #b9afd1;
        flex-shrink: 0;
      }
      .match-name {
        font-family: "Fraunces", serif;
        font-size: 1.3rem;
        font-weight: 500;
        margin: 0;
        color: #f6f1e7;
      }
      .match-meta {
        color: #8f84ad;
        font-size: 0.85rem;
        margin: 0.15rem 0 0 0;
      }
      .match-contact {
        margin-top: 1rem;
        padding: 0.9rem 1rem;
        background: rgba(232, 165, 72, 0.08);
        border: 1px solid rgba(232, 165, 72, 0.25);
        border-radius: 8px;
      }
      .match-contact-row {
        display: flex;
        gap: 0.6rem;
        font-size: 0.9rem;
        margin-bottom: 0.35rem;
      }
      .match-contact-row:last-child { margin-bottom: 0; }
      .match-contact-label {
        color: #8f84ad;
        min-width: 4.5rem;
      }
      .match-contact a {
        color: #e8a548;
        word-break: break-all;
      }
      .match-contact-none {
        color: #b9afd1;
        font-size: 0.9rem;
        margin: 0;
      }
      .match-unmatch {
        background: transparent;
        border: none;
        color: #8f84ad;
        font-size: 0.8rem;
        cursor: pointer;
        text-decoration: underline;
        padding: 0;
        margin-top: 1rem;
      }
      .match-unmatch:hover { color: #f472b6; }

      /* Circles (/circle, /invite/[code], and the request banner on /home) */
      .circle-invite-box {
        background: rgba(232, 165, 72, 0.08);
        border: 1px solid rgba(232, 165, 72, 0.3);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 2rem;
      }
      .circle-link-row {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-top: 0.75rem;
      }
      .circle-link-row .field-input { flex: 1; min-width: 14rem; }
      .circle-section-title {
        font-family: "Fraunces", serif;
        font-size: 1.25rem;
        font-weight: 500;
        color: #f6f1e7;
        margin: 2rem 0 0.75rem 0;
      }
      .circle-person-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.9rem;
      }
      .circle-banner {
        display: flex;
        align-items: center;
        gap: 1rem;
        flex-wrap: wrap;
        background: rgba(232, 165, 72, 0.08);
        border: 1px solid rgba(232, 165, 72, 0.3);
        border-radius: 12px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 1.25rem;
      }
      .circle-banner p { margin: 0; flex: 1; color: #f6f1e7; min-width: 12rem; }
      .circle-setting {
        display: flex;
        gap: 0.75rem;
        align-items: flex-start;
        margin-top: 2.5rem;
        padding-top: 1.25rem;
        border-top: 1px solid rgba(185, 175, 209, 0.15);
        color: #f6f1e7;
        font-size: 0.9rem;
      }
      .circle-setting p { margin: 0.25rem 0 0 0; color: #8f84ad; font-size: 0.85rem; }
      .invite-card {
        max-width: 28rem;
        margin: 3rem auto 0 auto;
        text-align: center;
      }
      .invite-avatar {
        width: 96px;
        height: 96px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid rgba(232, 165, 72, 0.5);
        margin-bottom: 1rem;
      }

      /* The moment a match happens on Discovery */
      .match-moment {
        text-align: center;
        padding: 2.5rem 1.5rem;
      }
      .match-moment-title {
        font-family: "Fraunces", serif;
        font-size: 2rem;
        font-weight: 500;
        color: #e8a548;
        margin: 0 0 0.5rem 0;
      }
      .match-moment p {
        color: #b9afd1;
        max-width: 30em;
        margin: 0 auto 1.5rem auto;
        line-height: 1.6;
      }
      .match-moment-actions {
        display: flex;
        gap: 0.75rem;
        justify-content: center;
        flex-wrap: wrap;
      }
      .discover-card {
        background: #241f3d;
        border: 1px solid rgba(185, 175, 209, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
      }
      .discover-card-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2rem;
        align-items: start;
      }
      @media (max-width: 860px) {
        .discover-card-grid { grid-template-columns: 1fr; }
      }
      /* Frame hugs the photo: capped height, natural width, no cropping
         or letterboxing - same lesson as the profile photo grid fix. */
      .discover-main-photo {
        display: block;
        max-width: 100%;
        max-height: 460px;
        width: auto;
        height: auto;
        margin: 0 auto;
        border-radius: 10px;
        border: 1px solid rgba(185, 175, 209, 0.25);
      }
      .discover-photo-placeholder {
        width: 100%;
        aspect-ratio: 1;
        max-width: 320px;
        margin: 0 auto;
        border-radius: 10px;
        background: #2c2650;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: "Fraunces", serif;
        font-size: 4rem;
        color: #b9afd1;
      }
      .discover-photo-tag {
        text-align: center;
        color: #e8a548;
        font-size: 0.85rem;
        margin-top: 0.5rem;
      }
      .discover-thumbs {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        justify-content: center;
        margin-top: 0.75rem;
      }
      .discover-thumb {
        height: 56px;
        width: auto;
        border-radius: 6px;
        border: 2px solid transparent;
        cursor: pointer;
        opacity: 0.7;
      }
      .discover-thumb-active {
        border-color: #e8a548;
        opacity: 1;
      }
      .discover-name {
        font-family: "Fraunces", serif;
        font-size: 1.75rem;
        font-weight: 500;
        margin: 0;
        color: #f6f1e7;
      }
      .discover-headline {
        color: #b9afd1;
        margin: 0.25rem 0 0 0;
      }
      .discover-label {
        color: #8f84ad;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 1.25rem 0 0.5rem 0;
      }
      .discover-intro {
        color: #f6f1e7;
        font-size: 1rem;
        line-height: 1.65;
        margin: 0;
      }
      .discover-actions {
        display: flex;
        gap: 0.75rem;
        margin-top: 1.75rem;
      }
      .discover-actions .cta { flex: 1; text-align: center; }
      .discover-pass-btn {
        flex: 1;
        background: transparent;
        border: 1px solid rgba(185, 175, 209, 0.4);
        color: #f6f1e7;
        font-weight: 600;
        font-size: 1rem;
        padding: 0.85rem 1.25rem;
        border-radius: 4px;
        cursor: pointer;
      }
      .discover-pass-btn:hover { border-color: #f6f1e7; }
      .discover-later-btn { border-style: dashed; color: #b9afd1; }
      .discover-about {
        margin-top: 1.25rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(185, 175, 209, 0.15);
      }
      .discover-about-row {
        display: grid;
        grid-template-columns: 7.5rem 1fr;
        gap: 0.75rem;
        font-size: 0.9rem;
        color: #f6f1e7;
        padding: 0.35rem 0;
      }
      .discover-about-label {
        color: #8f84ad;
      }
      .discover-actions { flex-wrap: wrap; }
      .discover-deferred-badge {
        display: inline-block;
        color: #e8a548;
        background: rgba(232, 165, 72, 0.1);
        border: 1px solid rgba(232, 165, 72, 0.3);
        border-radius: 999px;
        font-size: 0.75rem;
        padding: 0.2rem 0.65rem;
        margin: 0 0 0.5rem 0;
      }
      .discover-pass-btn:disabled, .discover-actions .cta:disabled { opacity: 0.5; cursor: default; }
      .discover-counter {
        color: #8f84ad;
        font-size: 0.85rem;
        text-align: right;
        margin-bottom: 0.75rem;
      }
      .discover-empty {
        text-align: center;
        padding: 3rem 1.5rem;
      }
      .discover-empty p {
        color: #b9afd1;
        max-width: 32em;
        margin: 0.75rem auto 1.5rem auto;
        line-height: 1.6;
      }

      .activity-details-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.25rem;
      }
      @media (max-width: 860px) {
        .activity-details-grid {
          grid-template-columns: 1fr;
        }
      }
      .activity-detail-card {
        padding: 1.25rem;
        border: 1px dashed rgba(185, 175, 209, 0.3);
        border-radius: 8px;
      }

      @media (max-width: 420px) {
        .headline {
          font-size: 1.15rem;
        }
      }
    `}</style>
  );
}
