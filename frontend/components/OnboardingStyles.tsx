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
        padding: 6vh 6vw 10vh;
      }

      .loading { color: #b9afd1; font-family: "Public Sans", sans-serif; padding: 4vh 6vw; }

      .wrap { max-width: 560px; margin: 0 auto; }

      .wordmark {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 2.5rem;
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
        margin: 0 0 3rem 0;
      }

      .section {
        margin-bottom: 2.75rem;
        padding-bottom: 2.75rem;
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
        margin: 0 0 1.25rem 0;
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
        margin-bottom: 1.75rem;
        padding-bottom: 1.75rem;
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
        background: rgba(124, 107, 175, 0.18);
        border-color: #7c6baf;
        color: #f6f1e7;
      }

      .chip-loved {
        background: rgba(232, 165, 72, 0.18);
        border-color: #e8a548;
        color: #f6f1e7;
      }

      .chip-heart {
        color: #e8a548;
        font-size: 0.85rem;
      }

      .chip-check {
        color: #7c6baf;
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

      @media (max-width: 420px) {
        .headline {
          font-size: 1.15rem;
        }
      }
    `}</style>
  );
}
