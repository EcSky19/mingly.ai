import Head from "next/head";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import AutocompleteField from "../components/AutocompleteField";
import PrivacyToggles from "../components/PrivacyToggles";
import OnboardingStyles from "../components/OnboardingStyles";

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

type LocationEntry = {
  id: string;
  savedId?: string;
  city: string;
  cityLat?: number;
  cityLon?: number;
  neighborhood: string;
  label: string;
  isPrimary: boolean;
};

const emptyLocationEntry = (isPrimary: boolean): LocationEntry => ({
  id: `local-${Math.random().toString(36).slice(2)}`,
  city: "",
  neighborhood: "",
  label: "",
  isPrimary,
});


export default function Onboarding() {
  const router = useRouter();
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [firstName, setFirstName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [shareCompany, setShareCompany] = useState(true);

  const [currentRole, setCurrentRole] = useState<FieldState>(emptyField());
  const [company, setCompany] = useState<FieldState>(emptyField());
  const [industry, setIndustry] = useState<FieldState>(emptyField());
  const [careerStage, setCareerStage] = useState("");
  const [education, setEducation] = useState<EducationEntry[]>([emptyEducationEntry()]);

  const [locations, setLocations] = useState<LocationEntry[]>([emptyLocationEntry(true)]);

  useEffect(() => {
    fetch(`${API_URL}/api/auth/me`, { credentials: "include" })
      .then((res) => {
        if (!res.ok) {
          router.replace("/");
          return null;
        }
        return res.json();
      })
      .then((data) => {
        if (data?.first_name) setFirstName(data.first_name);
      })
      .finally(() => setCheckingAuth(false));
  }, [router]);

  useEffect(() => {
    if (checkingAuth) return;

    // Restores previously saved role/company/industry/career stage on
    // reload - this fetch was missing before (education and locations
    // restored correctly, but professional profile silently didn't).
    fetch(`${API_URL}/api/profile/professional`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then(
        (
          data: {
            current_role?: string;
            company?: string;
            industry?: string;
            career_stage?: string;
          } | null
        ) => {
          if (!data) return;
          if (data.current_role) setCurrentRole({ ...emptyField(), value: data.current_role });
          if (data.company) {
            setCompany({ ...emptyField(), value: data.company });
            setShareCompany(true);
          } else if (data.industry) {
            setIndustry({ ...emptyField(), value: data.industry });
            setShareCompany(false);
          }
          if (data.career_stage) setCareerStage(data.career_stage);
        }
      )
      .catch(() => {});

    fetch(`${API_URL}/api/profile/education`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then(
        (
          rows: {
            id: string;
            school?: string;
            degree?: string;
            field_of_study?: string;
            graduation_year?: number;
            visible_on_profile: boolean;
            usable_for_matching: boolean;
          }[]
        ) => {
          if (rows.length === 0) return;
          setEducation(
            rows.map((r) => ({
              id: r.id,
              savedId: r.id,
              school: r.school || "",
              degree: r.degree || "",
              fieldOfStudy: r.field_of_study || "",
              graduationYear: r.graduation_year ? String(r.graduation_year) : "",
              visibleOnProfile: r.visible_on_profile,
              usableForMatching: r.usable_for_matching,
            }))
          );
        }
      )
      .catch(() => {});

    fetch(`${API_URL}/api/profile/locations`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then(
        (
          rows: {
            id: string;
            city?: string;
            neighborhood?: string;
            latitude?: number;
            longitude?: number;
            label?: string;
            is_primary: boolean;
          }[]
        ) => {
          if (rows.length === 0) return;
          setLocations(
            rows.map((r) => ({
              id: r.id,
              savedId: r.id,
              city: r.city || "",
              cityLat: r.latitude,
              cityLon: r.longitude,
              neighborhood: r.neighborhood || "",
              label: r.label || "",
              isPrimary: r.is_primary,
            }))
          );
        }
      )
      .catch(() => {});
  }, [checkingAuth]);

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

  function updateLocation(id: string, patch: Partial<LocationEntry>) {
    setLocations((prev) => prev.map((l) => (l.id === id ? { ...l, ...patch } : l)));
  }

  function setPrimaryLocation(id: string) {
    setLocations((prev) => prev.map((l) => ({ ...l, isPrimary: l.id === id })));
  }

  function addLocationEntry() {
    setLocations((prev) => [...prev, emptyLocationEntry(false)]);
  }

  async function removeLocationEntry(entry: LocationEntry) {
    setLocations((prev) => prev.filter((l) => l.id !== entry.id));
    if (entry.savedId) {
      try {
        await fetch(`${API_URL}/api/profile/locations/${entry.savedId}`, {
          method: "DELETE",
          credentials: "include",
        });
      } catch {
        // Fails open - same as education deletion.
      }
    }
  }

  async function saveLocationEntries() {
    const toSave = locations.filter((l) => !l.savedId && (l.city || l.neighborhood));
    for (const entry of toSave) {
      try {
        await fetch(`${API_URL}/api/profile/locations`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            city: entry.city || undefined,
            neighborhood: entry.neighborhood || undefined,
            latitude: entry.cityLat,
            longitude: entry.cityLon,
            label: entry.label || undefined,
            is_primary: entry.isPrimary,
          }),
        });
      } catch {
        // Fails open.
      }
    }
  }

  async function handleSave() {
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
      await saveLocationEntries();
      setSaved(true);
      router.push("/onboarding/interests");
    } catch {
      // Fails open - nothing here blocks the user from continuing even
      // if the save request fails; onboarding is not a validation gate.
      router.push("/onboarding/interests");
    } finally {
      setSaving(false);
    }
  }

  if (checkingAuth) {
    return (
      <main className="page">
        <p className="loading">Loading…</p>
        <OnboardingStyles />
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

          <h1 className="headline">{firstName ? `${firstName}'s` : "Your"} Mingly.ai Onboarding</h1>
          <p className="subhead">
            Every detail you add helps us find people you'll genuinely click
            with — people who share your interests, your pace, and your idea
            of a good time. You control what's visible on your profile, and
            information you shared is only used to help you find meaningful
            connections.
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

          <section className="section">
            <h2 className="section-title">Location</h2>
            {locations.map((entry, index) => (
              <div className="education-entry" key={entry.id}>
                {locations.length > 1 && (
                  <div className="education-entry-header">
                    <span className="education-entry-label">
                      {entry.isPrimary ? "Primary" : `Location ${index + 1}`}
                    </span>
                    <button
                      type="button"
                      className="remove-entry"
                      onClick={() => removeLocationEntry(entry)}
                    >
                      Remove
                    </button>
                  </div>
                )}
                <AutocompleteField
                  label="City"
                  placeholder="e.g. New York"
                  value={entry.city}
                  onChange={(v) => updateLocation(entry.id, { city: v, cityLat: undefined, cityLon: undefined })}
                  onSelectSuggestion={(s) =>
                    updateLocation(entry.id, {
                      city: s.value,
                      cityLat: s.latitude ?? undefined,
                      cityLon: s.longitude ?? undefined,
                    })
                  }
                  endpoint="/api/cities/autocomplete"
                  emptyHint="Not listed? What you've typed will be saved as-is."
                />
                <AutocompleteField
                  label="Neighborhood (optional)"
                  placeholder="e.g. Brooklyn"
                  value={entry.neighborhood}
                  onChange={(v) => updateLocation(entry.id, { neighborhood: v })}
                  endpoint="/api/neighborhoods/autocomplete"
                  extraQueryParams={{ near_lat: entry.cityLat, near_lon: entry.cityLon }}
                  disabled={!entry.city}
                  disabledHint="Enter a city first"
                  emptyHint="Not listed? What you've typed will be saved as-is."
                />
                <div className="field">
                  <label className="field-label">Label (optional)</label>
                  <input
                    className="field-input"
                    type="text"
                    placeholder="e.g. Home, or Work travel"
                    value={entry.label}
                    onChange={(e) => updateLocation(entry.id, { label: e.target.value })}
                  />
                </div>
                {locations.length > 1 && !entry.isPrimary && (
                  <button
                    type="button"
                    className="set-primary"
                    onClick={() => setPrimaryLocation(entry.id)}
                  >
                    Make this my primary location
                  </button>
                )}
              </div>
            ))}
            <button type="button" className="add-entry" onClick={addLocationEntry}>
              + Add another location
            </button>
            <p className="section-hint">
              Frequently visit a second city for work or lifestyle reasons? Add it — this is free
              and helps us match you accurately wherever you actually spend time.
            </p>
          </section>

          <div className="actions">
            <button
              type="button"
              className="cta"
              disabled={saving}
              onClick={() => handleSave()}
            >
              {saving ? "Saving…" : "Continue"}
            </button>
            <button
              type="button"
              className="skip"
              onClick={() => router.push("/onboarding/interests")}
            >
              Skip for now
            </button>
          </div>
          {saved && <p className="saved-hint">Saved.</p>}
        </div>
      </main>
      <OnboardingStyles />
    </>
  );
}
