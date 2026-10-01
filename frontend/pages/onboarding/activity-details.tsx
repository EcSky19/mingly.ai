import Head from "next/head";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import OnboardingStyles from "../../components/OnboardingStyles";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type ActivityRow = {
  activityId: string;
  name: string;
  category: string;
  isTopPick: boolean;
  interestStrength: string;
  desiredFrequency: string;
  visibleOnProfile: boolean;
};

// Third onboarding step: details for "loved" activities only (the top
// picks from /onboarding/interests). Split into its own page since
// filling out 5 fields per loved activity is a distinct task from
// picking interests/activities in the first place - keeps each page
// focused on one thing.
export default function ActivityDetails() {
  const router = useRouter();
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [firstName, setFirstName] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activities, setActivities] = useState<ActivityRow[]>([]);

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

    fetch(`${API_URL}/api/profile/activities`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then(
        (
          rows: {
            activity_id: string;
            name: string;
            category: string;
            is_top_pick: boolean;
            interest_strength?: string;
            desired_frequency?: string;
            visible_on_profile: boolean;
          }[]
        ) => {
          const mapped: ActivityRow[] = rows.map((r) => ({
            activityId: r.activity_id,
            name: r.name,
            category: r.category,
            isTopPick: r.is_top_pick,
            interestStrength: r.interest_strength || "",
            desiredFrequency: r.desired_frequency || "",
            visibleOnProfile: r.visible_on_profile,
          }));
          setActivities(mapped);

          // Nothing loved - nothing to configure here, skip straight ahead.
          if (!mapped.some((a) => a.isTopPick)) {
            router.push("/onboarding/social");
          }
        }
      )
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [checkingAuth, router]);

  function updateActivity(activityId: string, patch: Partial<ActivityRow>) {
    setActivities((prev) =>
      prev.map((a) => (a.activityId === activityId ? { ...a, ...patch } : a))
    );
  }

  async function handleFinish() {
    setSaving(true);
    try {
      await fetch(`${API_URL}/api/profile/activities`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          activities: activities.map((a) => ({
            activity_id: a.activityId,
            interest_strength: a.interestStrength || undefined,
            desired_frequency: a.desiredFrequency || undefined,
            is_top_pick: a.isTopPick,
            visible_on_profile: a.visibleOnProfile,
          })),
        }),
      });
      router.push("/onboarding/social");
    } catch {
      // Fails open - not a validation gate.
      router.push("/onboarding/social");
    } finally {
      setSaving(false);
    }
  }

  if (checkingAuth || loading) {
    return (
      <main className="page">
        <p className="loading">Loading…</p>
        <OnboardingStyles />
      </main>
    );
  }

  const loved = activities.filter((a) => a.isTopPick);

  return (
    <>
      <Head>
        <title>Activity Details — Mingly.ai</title>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Public+Sans:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </Head>
      <main className="page">
        <div className="profile-wrap">
          <span className="wordmark">
            <img src="/mingly-mark.png" alt="" className="mark" />
            <span>Mingly.ai</span>
          </span>

          <button
            type="button"
            className="back-link"
            onClick={() => router.push("/onboarding/interests")}
          >
            ← Back to interests & activities
          </button>

          <h1 className="headline">
            {firstName ? `${firstName}'s` : "Your"} Loved Activities
          </h1>
          <p className="subhead">
            A bit more about the activities you loved helps us suggest the right plan at the
            right time.
          </p>

          <div className="activity-details-grid">
            {loved.map((activity) => (
              <div className="activity-detail-card" key={activity.activityId}>
                <div className="education-entry-header">
                  <span className="education-entry-label">{activity.name}</span>
                </div>
                <div className="field">
                  <label className="field-label">How often would you like to do this?</label>
                  <select
                    className="field-input"
                    value={activity.desiredFrequency}
                    onChange={(e) =>
                      updateActivity(activity.activityId, { desiredFrequency: e.target.value })
                    }
                  >
                    <option value="">Select one</option>
                    <option value="rarely">Rarely</option>
                    <option value="monthly">Monthly</option>
                    <option value="weekly">Weekly</option>
                    <option value="multiple_times_per_week">Multiple times a week</option>
                  </select>
                </div>
              </div>
            ))}
          </div>

          <div className="actions">
            <button type="button" className="cta" disabled={saving} onClick={handleFinish}>
              {saving ? "Saving…" : "Finish"}
            </button>
            <button type="button" className="skip" onClick={() => router.push("/onboarding/social")}>
              Skip for now
            </button>
          </div>
        </div>
      </main>
      <OnboardingStyles />
    </>
  );
}
