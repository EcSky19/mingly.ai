import Head from "next/head";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import ChipSelect from "../../components/ChipSelect";
import OnboardingStyles from "../../components/OnboardingStyles";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  { value: "", label: "Select one" },
  { value: "ready_now", label: "Ready now" },
  { value: "sometime_soon", label: "Sometime soon" },
  { value: "when_season_right", label: "When the season's right" },
  { value: "no_rush", label: "No rush, just excited" },
];

const MAX_TOP_INTERESTS = 5;
const MAX_TOP_ACTIVITIES = 10;

// Split out from the main onboarding page: personal/professional info
// (role, education, location) rarely changes once filled in, but
// interests and activities are things people revisit more often - so
// they get their own page/step rather than living in one long form.
export default function OnboardingInterests() {
  const router = useRouter();
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [firstName, setFirstName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

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
  }, [checkingAuth]);

  function cycleInterest(id: string) {
    const isLoved = topInterestIds.includes(id);
    const isLiked = !isLoved && selectedInterestIds.includes(id);

    if (isLoved) {
      // loved -> unselected
      setTopInterestIds((prev) => prev.filter((x) => x !== id));
      setSelectedInterestIds((prev) => prev.filter((x) => x !== id));
    } else if (isLiked) {
      // liked -> loved, unless loved is already at capacity (stays liked)
      if (topInterestIds.length >= MAX_TOP_INTERESTS) return;
      setTopInterestIds((prev) => [...prev, id]);
    } else {
      // unselected -> liked
      setSelectedInterestIds((prev) => [...prev, id]);
    }
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

  function cycleActivity(id: string) {
    const isLoved = topActivityIds.includes(id);
    const isLiked = !isLoved && selectedActivityIds.includes(id);

    if (isLoved) {
      setTopActivityIds((prev) => prev.filter((x) => x !== id));
      setSelectedActivityIds((prev) => prev.filter((x) => x !== id));
    } else if (isLiked) {
      if (topActivityIds.length >= MAX_TOP_ACTIVITIES) return;
      setTopActivityIds((prev) => [...prev, id]);
    } else {
      setSelectedActivityIds((prev) => [...prev, id]);
      setActivityContext((prev) => (prev[id] ? prev : { ...prev, [id]: emptyActivityContext() }));
    }
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

  async function handleSave() {
    setSaving(true);
    try {
      await saveInterests();
      await saveActivities();
      setSaved(true);
      router.push("/home");
    } catch {
      router.push("/home");
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
        <title>Interests & Activities — Mingly.ai</title>
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

          <button type="button" className="back-link" onClick={() => router.push("/onboarding")}>
            ← Back to personal info
          </button>

          <h1 className="headline">
            {firstName ? `${firstName}'s` : "Your"} Interests & Activities
          </h1>
          <p className="subhead">
            This is where we find your people. Tell us what excites you and what you'd actually
            love to do with someone — it's how we connect you with people who get it, not just
            people who exist nearby.
          </p>

          <section className="section">
            <h2 className="section-title">Interests</h2>
            <p className="section-hint">
              Click once to like something, again to love it (up to {MAX_TOP_INTERESTS}), a third
              time to clear it.
            </p>
            <ChipSelect
              items={interestCatalog.map((i) => ({ id: i.id, label: i.name }))}
              selectedIds={selectedInterestIds}
              lovedIds={topInterestIds}
              maxLoved={MAX_TOP_INTERESTS}
              onCycle={cycleInterest}
            />
          </section>

          <section className="section">
            <h2 className="section-title">Activities</h2>
            <p className="section-hint">
              Things you'd actually do with someone — not just enjoy in theory. Click once to
              like, again to love (up to {MAX_TOP_ACTIVITIES}) — loved activities get the most
              weight in your recommendations.
            </p>
            <ChipSelect
              items={activityCatalog.map((a) => ({ id: a.id, label: a.name }))}
              selectedIds={selectedActivityIds}
              lovedIds={topActivityIds}
              maxLoved={MAX_TOP_ACTIVITIES}
              onCycle={cycleActivity}
            />

            {topActivityIds.length > 0 && (
              <div className="top-activity-context">
                <p className="section-hint">
                  A bit more about your loved activities helps us suggest the right plan:
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
                          <option value="">Select one</option>
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
                          <option value="">Select one</option>
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
                          <option value="">Select one</option>
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
                          <option value="">Select one</option>
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
            <button type="button" className="cta" disabled={saving} onClick={handleSave}>
              {saving ? "Saving…" : "Finish"}
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
