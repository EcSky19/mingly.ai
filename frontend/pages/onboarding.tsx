import Head from "next/head";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import AutocompleteField from "../components/AutocompleteField";
import PrivacyToggles from "../components/PrivacyToggles";
import ChipSelect from "../components/ChipSelect";
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

type CatalogItem = { id: string; name: string; category?: string };

type ActivityContext = {
  interestStrength: string;
  skillLevel: string;
  activityStyle: string;
  desiredFrequency: string;
  preferredGroupSize: string;
  targetTimeframe: string;
};

const emptyActivityContext = (): ActivityContext => ({
  interestStrength: "",
  skillLevel: "",
  activityStyle: "",
  desiredFrequency: "",
  preferredGroupSize: "",
  targetTimeframe: "",
});

const TARGET_TIMEFRAMES: { value: string; label: string }[] = [
  { value: "", label: "Prefer not to say" },
  { value: "ready_now", label: "Ready now" },
  { value: "sometime_soon", label: "Sometime soon" },
  { value: "when_season_right", label: "When the season's right" },
  { value: "no_rush", label: "No rush, just excited" },
];

const MAX_TOP_INTERESTS = 5;
const MAX_TOP_ACTIVITIES = 3;

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

  const [interestCatalog, setInterestCatalog] = useState<CatalogItem[]>([]);
  const [selectedInterestIds, setSelectedInterestIds] = useState<string[]>([]);
  const [topInterestIds, setTopInterestIds] = useState<string[]>([]);

  const [activityCatalog, setActivityCatalog] = useState<CatalogItem[]>([]);
  const [selectedActivityIds, setSelectedActivityIds] = useState<string[]>([]);
  const [topActivityIds, setTopActivityIds] = useState<string[]>([]);
  const [activityContext, setActivityContext] = useState<Record<string, ActivityContext>>({});

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

    fetch(`${API_URL}/api/catalog/interests`)
      .then((r) => r.json())
      .then(setInterestCatalog)
      .catch(() => setInterestCatalog([]));

    fetch(`${API_URL}/api/catalog/activities`)
      .then((r) => r.json())
      .then(setActivityCatalog)
      .catch(() => setActivityCatalog([]));

    fetch(`${API_URL}/api/profile/interests`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((rows: { interest_id: string; is_top_pick: boolean }[]) => {
        if (rows.length === 0) return;
        setSelectedInterestIds(rows.map((r) => r.interest_id));
        setTopInterestIds(rows.filter((r) => r.is_top_pick).map((r) => r.interest_id));
      })
      .catch(() => {});

    fetch(`${API_URL}/api/profile/activities`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then(
        (
          rows: {
            activity_id: string;
            is_top_pick: boolean;
            interest_strength?: string;
            skill_level?: string;
            activity_style?: string;
            desired_frequency?: string;
            preferred_group_size?: string;
            target_timeframe?: string;
          }[]
        ) => {
          if (rows.length === 0) return;
          setSelectedActivityIds(rows.map((r) => r.activity_id));
          setTopActivityIds(rows.filter((r) => r.is_top_pick).map((r) => r.activity_id));
          const ctx: Record<string, ActivityContext> = {};
          rows.forEach((r) => {
            ctx[r.activity_id] = {
              interestStrength: r.interest_strength || "",
              skillLevel: r.skill_level || "",
              activityStyle: r.activity_style || "",
              desiredFrequency: r.desired_frequency || "",
              preferredGroupSize: r.preferred_group_size || "",
              targetTimeframe: r.target_timeframe || "",
            };
          });
          setActivityContext(ctx);
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

  function toggleInterest(id: string) {
    setSelectedInterestIds((prev) => {
      if (prev.includes(id)) {
        setTopInterestIds((t) => t.filter((x) => x !== id));
        return prev.filter((x) => x !== id);
      }
      return [...prev, id];
    });
  }

  function toggleTopInterest(id: string) {
    setTopInterestIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= MAX_TOP_INTERESTS) return prev;
      return [...prev, id];
    });
  }

  async function saveInterests() {
    if (selectedInterestIds.length === 0) return;
    try {
      await fetch(`${API_URL}/api/profile/interests`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          interest_ids: selectedInterestIds,
          top_pick_ids: topInterestIds,
          visible_on_profile: true,
        }),
      });
    } catch {
      // Fails open.
    }
  }

  function toggleActivity(id: string) {
    setSelectedActivityIds((prev) => {
      if (prev.includes(id)) {
        setTopActivityIds((t) => t.filter((x) => x !== id));
        return prev.filter((x) => x !== id);
      }
      return [...prev, id];
    });
    setActivityContext((prev) => (prev[id] ? prev : { ...prev, [id]: emptyActivityContext() }));
  }

  function toggleTopActivity(id: string) {
    setTopActivityIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= MAX_TOP_ACTIVITIES) return prev;
      return [...prev, id];
    });
  }

  function updateActivityContext(id: string, patch: Partial<ActivityContext>) {
    setActivityContext((prev) => ({
      ...prev,
      [id]: { ...(prev[id] || emptyActivityContext()), ...patch },
    }));
  }

  async function saveActivities() {
    if (selectedActivityIds.length === 0) return;
    try {
      await fetch(`${API_URL}/api/profile/activities`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          activities: selectedActivityIds.map((id) => {
            const ctx = activityContext[id] || emptyActivityContext();
            return {
              activity_id: id,
              interest_strength: ctx.interestStrength || undefined,
              skill_level: ctx.skillLevel || undefined,
              activity_style: ctx.activityStyle || undefined,
              desired_frequency: ctx.desiredFrequency || undefined,
              preferred_group_size: ctx.preferredGroupSize || undefined,
              is_top_pick: topActivityIds.includes(id),
              target_timeframe: ctx.targetTimeframe || undefined,
              visible_on_profile: true,
            };
          }),
        }),
      });
    } catch {
      // Fails open.
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
      await saveLocationEntries();
      await saveInterests();
      await saveActivities();
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

          <section className="section">
            <h2 className="section-title">Interests</h2>
            <p className="section-hint">
              Things you enjoy. Star up to {MAX_TOP_INTERESTS} that matter most to you.
            </p>
            <ChipSelect
              items={interestCatalog.map((i) => ({ id: i.id, label: i.name }))}
              selectedIds={selectedInterestIds}
              topPickIds={topInterestIds}
              maxTopPicks={MAX_TOP_INTERESTS}
              onToggleSelect={toggleInterest}
              onToggleTopPick={toggleTopInterest}
            />
          </section>

          <section className="section">
            <h2 className="section-title">Activities</h2>
            <p className="section-hint">
              Things you'd actually do with someone — not just enjoy in theory. Star up to{" "}
              {MAX_TOP_ACTIVITIES} you genuinely want to do this month; those get the most weight
              in your recommendations.
            </p>
            <ChipSelect
              items={activityCatalog.map((a) => ({ id: a.id, label: a.name }))}
              selectedIds={selectedActivityIds}
              topPickIds={topActivityIds}
              maxTopPicks={MAX_TOP_ACTIVITIES}
              onToggleSelect={toggleActivity}
              onToggleTopPick={toggleTopActivity}
            />

            {topActivityIds.length > 0 && (
              <div className="top-activity-context">
                <p className="section-hint">
                  A bit more about your top picks helps us suggest the right plan:
                </p>
                {topActivityIds.map((id) => {
                  const activity = activityCatalog.find((a) => a.id === id);
                  const ctx = activityContext[id] || emptyActivityContext();
                  if (!activity) return null;
                  return (
                    <div className="education-entry" key={id}>
                      <div className="education-entry-header">
                        <span className="education-entry-label">{activity.name}</span>
                      </div>
                      <div className="field">
                        <label className="field-label">Skill level</label>
                        <select
                          className="field-input"
                          value={ctx.skillLevel}
                          onChange={(e) => updateActivityContext(id, { skillLevel: e.target.value })}
                        >
                          <option value="">Prefer not to say</option>
                          <option value="beginner">Beginner</option>
                          <option value="intermediate">Intermediate</option>
                          <option value="advanced">Advanced</option>
                          <option value="competitive">Competitive</option>
                        </select>
                      </div>
                      <div className="field">
                        <label className="field-label">Style</label>
                        <select
                          className="field-input"
                          value={ctx.activityStyle}
                          onChange={(e) => updateActivityContext(id, { activityStyle: e.target.value })}
                        >
                          <option value="">Prefer not to say</option>
                          <option value="casual_social">Casual / social</option>
                          <option value="fitness_focused">Fitness-focused</option>
                          <option value="competitive">Competitive</option>
                          <option value="exploratory">Exploratory (trying new things)</option>
                        </select>
                      </div>
                      <div className="field">
                        <label className="field-label">How often would you like to do this?</label>
                        <select
                          className="field-input"
                          value={ctx.desiredFrequency}
                          onChange={(e) =>
                            updateActivityContext(id, { desiredFrequency: e.target.value })
                          }
                        >
                          <option value="">Prefer not to say</option>
                          <option value="rarely">Rarely</option>
                          <option value="monthly">Monthly</option>
                          <option value="weekly">Weekly</option>
                          <option value="multiple_times_per_week">Multiple times a week</option>
                        </select>
                      </div>
                      <div className="field">
                        <label className="field-label">Preferred group size</label>
                        <select
                          className="field-input"
                          value={ctx.preferredGroupSize}
                          onChange={(e) =>
                            updateActivityContext(id, { preferredGroupSize: e.target.value })
                          }
                        >
                          <option value="">Prefer not to say</option>
                          <option value="one_on_one">1-on-1</option>
                          <option value="small_group">Small group</option>
                          <option value="either">Either</option>
                        </select>
                      </div>
                      <div className="field">
                        <label className="field-label">When would you like to do this?</label>
                        <select
                          className="field-input"
                          value={ctx.targetTimeframe}
                          onChange={(e) =>
                            updateActivityContext(id, { targetTimeframe: e.target.value })
                          }
                        >
                          {TARGET_TIMEFRAMES.map((t) => (
                            <option key={t.value} value={t.value}>
                              {t.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
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
      <OnboardingStyles />
    </>
  );
}
