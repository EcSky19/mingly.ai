import Head from "next/head";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import AutocompleteField from "../components/AutocompleteField";
import PrivacyToggles from "../components/PrivacyToggles";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type FieldState = {
  value: string;
  visibleOnProfile: boolean;
  usableForMatching: boolean;
};

const emptyField = (): FieldState => ({
  value: "",
  visibleOnProfile: false,
  usableForMatching: true,
});

type EducationEntry = {
  id: string; // client-side temp id, or real id once saved
  savedId?: string; // set once persisted to the backend
  school: string;
  degree: string;
  fieldOfStudy: string;
  graduationYear: string;
  visibleOnProfile: boolean;
  usableForMatching: boolean;
};

const emptyEducationEntry = (): EducationEntry => ({
  id: `local-${Math.random().toString(36).slice(2)}`,
  school: "",
  degree: "",
  fieldOfStudy: "",
  graduationYear: "",
  visibleOnProfile: false,
  usableForMatching: true,
});

const CAREER_STAGES: { value: string; label: string }[] = [
  { value: "student", label: "Student" },
  { value: "early_career", label: "Early career" },
  { value: "mid_career", label: "Mid career" },
  { value: "senior", label: "Senior" },
  { value: "founder", label: "Founder" },
  { value: "graduate_student", label: "Graduate student" },
  { value: "career_transition", label: "Career transition" },
  { value: "other", label: "Other" },
];

export default function Onboarding() {
  const router = useRouter();
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [shareCompany, setShareCompany] = useState(true);

  const [currentRole, setCurrentRole] = useState<FieldState>(emptyField());
  const [company, setCompany] = useState<FieldState>(emptyField());
  const [industry, setIndustry] = useState<FieldState>(emptyField());
  const [careerStage, setCareerStage] = useState("");
  const [education, setEducation] = useState<EducationEntry[]>([emptyEducationEntry()]);

  useEffect(() => {
    fetch(`${API_URL}/api/auth/me`, { credentials: "include" })
      .then((res) => {
        if (!res.ok) {
          router.replace("/");
          return null;
        }
        return res.json();
      })
      .finally(() => setCheckingAuth(false));
  }, [router]);

  function updateEducation(id: string, patch: Partial<EducationEntry>) {
    setEducation((prev) => prev.map((e) => (e.id === id ? { ...e, ...patch } : e)));
  }

  function addEducationEntry() {
    setEducation((prev) => [...prev, emptyEducationEntry()]);
  }

  async function removeEducationEntry(entry: EducationEntry) {
    setEducation((prev) => prev.filter((e) => e.id !== entry.id));
    if (entry.savedId) {
      try {
        await fetch(`${API_URL}/api/profile/education/${entry.savedId}`, {
          method: "DELETE",
          credentials: "include",
        });
      } catch {
        // Fails open - the entry is already gone from the UI; a failed
        // delete call here isn't worth blocking the user over.
      }
    }
  }

  function fieldPayload(f: FieldState) {
    if (!f.value.trim()) return undefined;
    return {
      value: f.value,
      visible_on_profile: f.visibleOnProfile,
      usable_for_matching: f.usableForMatching,
    };
  }

  async function saveEducationEntries() {
    const toSave = education.filter(
      (e) => !e.savedId && (e.school || e.degree || e.fieldOfStudy || e.graduationYear)
    );
    for (const entry of toSave) {
      try {
        await fetch(`${API_URL}/api/profile/education`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            school: entry.school || undefined,
            degree: entry.degree || undefined,
            field_of_study: entry.fieldOfStudy || undefined,
            graduation_year: entry.graduationYear ? parseInt(entry.graduationYear, 10) : undefined,
            visible_on_profile: entry.visibleOnProfile,
            usable_for_matching: entry.usableForMatching,
          }),
        });
      } catch {
        // Fails open - one failed entry save doesn't block the rest of onboarding.
      }
    }
  }

  async function handleSave(skipRest: boolean) {
    setSaving(true);
    try {
      const body = {
        current_role: fieldPayload(currentRole),
        company: shareCompany ? fieldPayload(company) : undefined,
        industry: !shareCompany ? fieldPayload(industry) : undefined,
        career_stage: careerStage || undefined,
      };
      await fetch(`${API_URL}/api/profile/professional`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(body),
      });
      await saveEducationEntries();
      setSaved(true);
      if (skipRest) router.push("/home");
    } catch {
      // Fails open - nothing here blocks the user from continuing even
      // if the save request fails; onboarding is not a validation gate.
      if (skipRest) router.push("/home");
    } finally {
      setSaving(false);
    }
  }

  if (checkingAuth) {
    return (
      <main className="page">
        <p className="loading">Loading…</p>
        <PageStyles />
      </main>
    );
  }

  return (
    <>
      <Head>
        <title>Tell us about your professional context — Mingly.ai</title>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Public+Sans:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </Head>
      <main className="page">
        <div className="wrap">
          <span className="wordmark">
            <img src="/mingly-mark.png" alt="" className="mark" />
            <span>Mingly.ai</span>
          </span>

          <h1 className="headline">Your professional context</h1>
          <p className="subhead">
            Everything below is optional. It helps us find people you'll
            actually click with — nothing here is required, and you choose
            what's visible versus just used for matching.
          </p>

          <section className="section">
            <h2 className="section-title">Role</h2>
            <AutocompleteField
              label="Current role"
              placeholder="e.g. Software Engineer"
              value={currentRole.value}
              onChange={(v) => setCurrentRole({ ...currentRole, value: v })}
              endpoint="/api/job-titles/autocomplete"
            />
            <PrivacyToggles
              visibleOnProfile={currentRole.visibleOnProfile}
              usableForMatching={currentRole.usableForMatching}
              onChangeVisible={(v) => setCurrentRole({ ...currentRole, visibleOnProfile: v })}
              onChangeMatching={(v) => setCurrentRole({ ...currentRole, usableForMatching: v })}
            />
          </section>

          <section className="section">
            <div className="section-header-row">
              <h2 className="section-title">Current Employment</h2>
              <div className="toggle-pair">
                <button
                  type="button"
                  className={shareCompany ? "toggle-btn active" : "toggle-btn"}
                  onClick={() => setShareCompany(true)}
                >
                  Share Company
                </button>
                <button
                  type="button"
                  className={!shareCompany ? "toggle-btn active" : "toggle-btn"}
                  onClick={() => setShareCompany(false)}
                >
                  Share Industry
                </button>
              </div>
            </div>

            {shareCompany ? (
              <>
                <AutocompleteField
                  label="Company"
                  placeholder="e.g. Google"
                  value={company.value}
                  onChange={(v) => setCompany({ ...company, value: v })}
                  endpoint="/api/companies/autocomplete"
                />
                <PrivacyToggles
                  visibleOnProfile={company.visibleOnProfile}
                  usableForMatching={company.usableForMatching}
                  onChangeVisible={(v) => setCompany({ ...company, visibleOnProfile: v })}
                  onChangeMatching={(v) => setCompany({ ...company, usableForMatching: v })}
                />
              </>
            ) : (
              <>
                <AutocompleteField
                  label="Industry"
                  placeholder="e.g. Technology"
                  value={industry.value}
                  onChange={(v) => setIndustry({ ...industry, value: v })}
                  endpoint="/api/industries/autocomplete"
                />
                <PrivacyToggles
                  visibleOnProfile={industry.visibleOnProfile}
                  usableForMatching={industry.usableForMatching}
                  onChangeVisible={(v) => setIndustry({ ...industry, visibleOnProfile: v })}
                  onChangeMatching={(v) => setIndustry({ ...industry, usableForMatching: v })}
                />
              </>
            )}
          </section>

          <section className="section">
            <h2 className="section-title">Career stage</h2>
            <div className="field">
              <select
                className="field-input"
                value={careerStage}
                onChange={(e) => setCareerStage(e.target.value)}
              >
                <option value="">Prefer not to say</option>
                {CAREER_STAGES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
          </section>

          <section className="section">
            <h2 className="section-title">Education</h2>
            {education.map((entry, index) => (
              <div className="education-entry" key={entry.id}>
                {education.length > 1 && (
                  <div className="education-entry-header">
                    <span className="education-entry-label">
                      {index === 0 ? "First degree" : `Degree ${index + 1}`}
                    </span>
                    <button
                      type="button"
                      className="remove-entry"
                      onClick={() => removeEducationEntry(entry)}
                    >
                      Remove
                    </button>
                  </div>
                )}
                <AutocompleteField
                  label="School"
                  placeholder="e.g. Cornell University"
                  value={entry.school}
                  onChange={(v) => updateEducation(entry.id, { school: v })}
                  endpoint="/api/schools/autocomplete"
                  emptyHint="Can't find your school? What you've typed will be saved as-is."
                />
                <AutocompleteField
                  label="Degree"
                  placeholder="e.g. Bachelor of Science (BS)"
                  value={entry.degree}
                  onChange={(v) => updateEducation(entry.id, { degree: v })}
                  endpoint="/api/degrees/autocomplete"
                />
                <AutocompleteField
                  label="Field of study"
                  placeholder="e.g. Computer Science"
                  value={entry.fieldOfStudy}
                  onChange={(v) => updateEducation(entry.id, { fieldOfStudy: v })}
                  endpoint="/api/fields-of-study/autocomplete"
                />
                <div className="field">
                  <label className="field-label">Graduation year</label>
                  <input
                    className="field-input"
                    type="number"
                    placeholder="e.g. 2022"
                    value={entry.graduationYear}
                    onChange={(e) => updateEducation(entry.id, { graduationYear: e.target.value })}
                    min={1950}
                    max={2035}
                  />
                </div>
                <PrivacyToggles
                  visibleOnProfile={entry.visibleOnProfile}
                  usableForMatching={entry.usableForMatching}
                  onChangeVisible={(v) => updateEducation(entry.id, { visibleOnProfile: v })}
                  onChangeMatching={(v) => updateEducation(entry.id, { usableForMatching: v })}
                />
              </div>
            ))}
            <button type="button" className="add-entry" onClick={addEducationEntry}>
              + Add another degree
            </button>
          </section>

          <div className="actions">
            <button
              type="button"
              className="cta"
              disabled={saving}
              onClick={() => handleSave(true)}
            >
              {saving ? "Saving…" : "Continue"}
            </button>
            <button type="button" className="skip" onClick={() => router.push("/home")}>
              Skip for now
            </button>
          </div>
          {saved && <p className="saved-hint">Saved.</p>}
        </div>
      </main>
      <PageStyles />
    </>
  );
}

function PageStyles() {
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
        font-size: clamp(1.9rem, 4vw, 2.6rem);
        line-height: 1.1;
        margin: 0 0 0.75rem 0;
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
      .saved-hint { color: #8f84ad; font-size: 0.85rem; margin-top: 1rem; }
    `}</style>
  );
}
