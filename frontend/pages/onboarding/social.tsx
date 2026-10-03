import Head from "next/head";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import PrivacyToggles from "../../components/PrivacyToggles";
import MultiSelectChips from "../../components/MultiSelectChips";
import OnboardingStyles from "../../components/OnboardingStyles";
import CollapsibleSection from "../../components/CollapsibleSection";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const CAREER_ORIENTATIONS = [
  { value: "", label: "Select one" },
  { value: "career_focused_building_life_outside", label: "Career-focused, but building more life outside work" },
  { value: "very_career_driven", label: "Very career-driven" },
  { value: "entrepreneurial", label: "Entrepreneurial / building something" },
  { value: "grad_or_professional_school", label: "Graduate / professional school focused" },
  { value: "established_expanding_social_life", label: "Established professionally, expanding social life" },
  { value: "balanced", label: "Balanced career and personal life" },
];

const CAREER_QUALITIES = [
  { value: "ambitious", label: "Ambitious" },
  { value: "curious", label: "Curious" },
  { value: "active", label: "Active" },
  { value: "creative", label: "Creative" },
  { value: "entrepreneurial", label: "Entrepreneurial" },
  { value: "intellectually_engaged", label: "Intellectually engaged" },
  { value: "laid_back", label: "Laid-back" },
  { value: "adventurous", label: "Adventurous" },
];

const EARLY_BIRD_NIGHT_OWL = [
  { value: "", label: "Select one" },
  { value: "early_bird", label: "Early bird" },
  { value: "night_owl", label: "Night owl" },
  { value: "either", label: "Either" },
];

const ACTIVITY_LEVELS = [
  { value: "", label: "Select one" },
  { value: "active", label: "Active" },
  { value: "moderate", label: "Moderate" },
  { value: "relaxed", label: "Relaxed" },
];

const DRINKING_PREFERENCES = [
  { value: "", label: "Select one" },
  { value: "non_drinker", label: "Non-drinker" },
  { value: "social_drinker", label: "Social drinker" },
  { value: "regular_drinker", label: "Regular drinker" },
  { value: "prefer_not_to_say", label: "Prefer not to say" },
];

const GOING_OUT_FREQUENCIES = [
  { value: "", label: "Select one" },
  { value: "rarely", label: "Rarely" },
  { value: "sometimes", label: "Sometimes" },
  { value: "often", label: "Often" },
  { value: "very_often", label: "Very often" },
];

const INDOOR_OUTDOOR_PREFERENCES = [
  { value: "", label: "Select one" },
  { value: "indoor", label: "Indoor" },
  { value: "outdoor", label: "Outdoor" },
  { value: "either", label: "Either" },
];

const WEEKDAY_WEEKEND_PREFERENCES = [
  { value: "", label: "Select one" },
  { value: "weekdays", label: "Weekdays" },
  { value: "weekends", label: "Weekends" },
  { value: "either", label: "Either" },
];

const SOCIAL_CADENCES = [
  { value: "", label: "Select one" },
  { value: "multiple_times_per_week", label: "Multiple times a week" },
  { value: "about_once_per_week", label: "About once a week" },
  { value: "a_few_times_per_month", label: "A few times a month" },
  { value: "occasionally", label: "Occasionally" },
];

const PLANNING_STYLES = [
  { value: "", label: "Select one" },
  { value: "spontaneous", label: "Spontaneous" },
  { value: "a_day_or_two_ahead", label: "A day or two ahead" },
  { value: "several_days_ahead", label: "Several days ahead" },
  { value: "about_a_week_ahead", label: "About a week ahead" },
  { value: "flexible", label: "Flexible" },
];

const MEETING_PREFERENCES = [
  { value: "", label: "Select one" },
  { value: "one_on_one", label: "1-on-1" },
  { value: "small_groups", label: "Small groups" },
  { value: "either", label: "Either" },
  { value: "prefer_bringing_someone_known", label: "Prefer bringing someone I know" },
];

const SOCIAL_ENVIRONMENTS = [
  { value: "conversation_focused", label: "Conversation-focused" },
  { value: "activity_focused", label: "Activity-focused" },
  { value: "low_key", label: "Low-key" },
  { value: "lively", label: "Lively" },
  { value: "outdoors", label: "Outdoors" },
  { value: "anything", label: "Anything" },
];

const SOCIAL_GOALS = [
  { value: "regular_friends", label: "New Friends" },
  { value: "activity_partners", label: "Activity partners" },
  { value: "broader_social_circle", label: "A broader social circle" },
  { value: "people_with_similar_lifestyles", label: "People with similar lifestyles" },
  { value: "professional_peers", label: "Social connections with professional peers" },
];

const SPENDING_PREFERENCES = [
  { value: "", label: "Select one" },
  { value: "inexpensive", label: "Prefer inexpensive plans" },
  { value: "moderate", label: "Moderate" },
  { value: "occasional_splurge", label: "Occasionally like to splurge" },
  { value: "premium", label: "Prefer premium experiences" },
  { value: "depends_on_activity", label: "Depends on the activity" },
];

const CITY_CIRCLE_STATUSES = [
  { value: "", label: "Select one" },
  { value: "new_here", label: "I'm new here" },
  { value: "know_some_want_to_expand", label: "I know some people but want to expand" },
  { value: "have_circle_want_more", label: "I already have a social circle but want to meet more people" },
  { value: "mainly_activity_partners", label: "I'm mainly looking for specific activity partners" },
];

// Final onboarding step: lifestyle, career/life orientation, and social
// preferences. Everything here is optional, single-row-per-user data
// (see docs and UserSocialProfile model) - one group-level privacy
// toggle rather than per-field, since ~13 fields would be too much UI
// otherwise.
export default function OnboardingSocial() {
  const router = useRouter();
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [firstName, setFirstName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const [careerOrientation, setCareerOrientation] = useState("");
  const [careerQualities, setCareerQualities] = useState<string[]>([]);
  const [earlyBirdNightOwl, setEarlyBirdNightOwl] = useState("");
  const [activityLevel, setActivityLevel] = useState("");
  const [drinkingPreference, setDrinkingPreference] = useState("");
  const [goingOutFrequency, setGoingOutFrequency] = useState("");
  const [indoorOutdoorPreference, setIndoorOutdoorPreference] = useState("");
  const [weekdayWeekendPreference, setWeekdayWeekendPreference] = useState("");
  const [socialCadence, setSocialCadence] = useState("");
  const [planningStyle, setPlanningStyle] = useState("");
  const [meetingPreference, setMeetingPreference] = useState("");
  const [socialEnvironment, setSocialEnvironment] = useState<string[]>([]);
  const [socialGoals, setSocialGoals] = useState<string[]>([]);
  const [spendingPreference, setSpendingPreference] = useState("");
  const [cityCircleStatus, setCityCircleStatus] = useState("");
  const [comfortableWithDogs, setComfortableWithDogs] = useState(false);
  const [visibleOnProfile, setVisibleOnProfile] = useState(false);
  const [usableForMatching, setUsableForMatching] = useState(true);

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

    fetch(`${API_URL}/api/profile/social`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then(
        (
          data: {
            career_orientation?: string;
            career_qualities?: string[];
            early_bird_night_owl?: string;
            activity_level?: string;
            drinking_preference?: string;
            going_out_frequency?: string;
            indoor_outdoor_preference?: string;
            weekday_weekend_preference?: string;
            social_cadence?: string;
            planning_style?: string;
            meeting_preference?: string;
            social_environment?: string[];
            social_goals?: string[];
            spending_preference?: string;
            city_circle_status?: string;
            comfortable_with_dogs?: boolean;
            visible_on_profile?: boolean;
            usable_for_matching?: boolean;
          } | null
        ) => {
          if (!data) return;
          setCareerOrientation(data.career_orientation || "");
          setCareerQualities(data.career_qualities || []);
          setEarlyBirdNightOwl(data.early_bird_night_owl || "");
          setActivityLevel(data.activity_level || "");
          setDrinkingPreference(data.drinking_preference || "");
          setGoingOutFrequency(data.going_out_frequency || "");
          setIndoorOutdoorPreference(data.indoor_outdoor_preference || "");
          setWeekdayWeekendPreference(data.weekday_weekend_preference || "");
          setSocialCadence(data.social_cadence || "");
          setPlanningStyle(data.planning_style || "");
          setMeetingPreference(data.meeting_preference || "");
          setSocialEnvironment(data.social_environment || []);
          setSocialGoals(data.social_goals || []);
          setSpendingPreference(data.spending_preference || "");
          setCityCircleStatus(data.city_circle_status || "");
          setComfortableWithDogs(data.comfortable_with_dogs || false);
          setVisibleOnProfile(data.visible_on_profile || false);
          setUsableForMatching(data.usable_for_matching ?? true);
        }
      )
      .catch(() => {});
  }, [checkingAuth]);

  function toggleCareerQuality(value: string) {
    setCareerQualities((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
    );
  }

  function toggleSocialEnvironment(value: string) {
    setSocialEnvironment((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
    );
  }

  function toggleSocialGoal(value: string) {
    setSocialGoals((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
    );
  }

  // Every path through onboarding converges on this page, so leaving it
  // (Finish or Skip) is what marks onboarding complete - matching
  // requires that flag, and the login redirect uses it to send returning
  // users to /home rather than back into onboarding.
  async function finishOnboarding() {
    try {
      await fetch(`${API_URL}/api/auth/onboarding-complete`, { method: "POST", credentials: "include" });
    } catch {
      // Fails open - they can still continue; worst case this is retried
      // next time they pass through this page.
    }
    router.push("/home");
  }

  async function handleSave() {
    setSaving(true);
    try {
      await fetch(`${API_URL}/api/profile/social`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          career_orientation: careerOrientation || null,
          career_qualities: careerQualities.length ? careerQualities : null,
          early_bird_night_owl: earlyBirdNightOwl || null,
          activity_level: activityLevel || null,
          drinking_preference: drinkingPreference || null,
          going_out_frequency: goingOutFrequency || null,
          indoor_outdoor_preference: indoorOutdoorPreference || null,
          weekday_weekend_preference: weekdayWeekendPreference || null,
          social_cadence: socialCadence || null,
          planning_style: planningStyle || null,
          meeting_preference: meetingPreference || null,
          social_environment: socialEnvironment.length ? socialEnvironment : null,
          social_goals: socialGoals.length ? socialGoals : null,
          spending_preference: spendingPreference || null,
          city_circle_status: cityCircleStatus || null,
          comfortable_with_dogs: comfortableWithDogs,
          visible_on_profile: visibleOnProfile,
          usable_for_matching: usableForMatching,
        }),
      });
      setSaved(true);
      await finishOnboarding();
    } catch {
      await finishOnboarding();
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
        <title>Lifestyle & Social — Mingly.ai</title>
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

          <h1 className="headline">
            {firstName ? `${firstName}'s` : "Your"} Lifestyle & Social Style
          </h1>
          <p className="subhead">
            The last piece — how you like to spend your time and meet people. Everything here is
            optional, and you decide what's shared versus just used to find better matches.
          </p>

          <CollapsibleSection
            title="Career & Life Orientation"
            defaultOpen
            summary={CAREER_ORIENTATIONS.find((o) => o.value === careerOrientation)?.label}
          >
            <div className="field">
              <label className="field-label">How would you describe your current focus?</label>
              <select
                className="field-input"
                value={careerOrientation}
                onChange={(e) => setCareerOrientation(e.target.value)}
              >
                {CAREER_ORIENTATIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <p className="section-hint">Qualities you'd use to describe yourself:</p>
            <MultiSelectChips
              options={CAREER_QUALITIES}
              selectedValues={careerQualities}
              onToggle={toggleCareerQuality}
            />
          </CollapsibleSection>

          <CollapsibleSection
            title="Lifestyle"
            defaultOpen
            summary={
              [
                earlyBirdNightOwl,
                activityLevel,
                drinkingPreference,
                goingOutFrequency,
                indoorOutdoorPreference,
                weekdayWeekendPreference,
              ].filter(Boolean).length > 0
                ? `${
                    [
                      earlyBirdNightOwl,
                      activityLevel,
                      drinkingPreference,
                      goingOutFrequency,
                      indoorOutdoorPreference,
                      weekdayWeekendPreference,
                    ].filter(Boolean).length
                  } of 6 set`
                : undefined
            }
          >
            <div className="field">
              <label className="field-label">Early bird or night owl?</label>
              <select
                className="field-input"
                value={earlyBirdNightOwl}
                onChange={(e) => setEarlyBirdNightOwl(e.target.value)}
              >
                {EARLY_BIRD_NIGHT_OWL.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label className="field-label">Activity level</label>
              <select
                className="field-input"
                value={activityLevel}
                onChange={(e) => setActivityLevel(e.target.value)}
              >
                {ACTIVITY_LEVELS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label className="field-label">Drinking preference</label>
              <select
                className="field-input"
                value={drinkingPreference}
                onChange={(e) => setDrinkingPreference(e.target.value)}
              >
                {DRINKING_PREFERENCES.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label className="field-label">How often do you go out?</label>
              <select
                className="field-input"
                value={goingOutFrequency}
                onChange={(e) => setGoingOutFrequency(e.target.value)}
              >
                {GOING_OUT_FREQUENCIES.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label className="field-label">Indoor or outdoor?</label>
              <select
                className="field-input"
                value={indoorOutdoorPreference}
                onChange={(e) => setIndoorOutdoorPreference(e.target.value)}
              >
                {INDOOR_OUTDOOR_PREFERENCES.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label className="field-label">Weekdays or weekends?</label>
              <select
                className="field-input"
                value={weekdayWeekendPreference}
                onChange={(e) => setWeekdayWeekendPreference(e.target.value)}
              >
                {WEEKDAY_WEEKEND_PREFERENCES.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          </CollapsibleSection>

          <CollapsibleSection
            title="Social Style"
            defaultOpen
            summary={
              [socialCadence, planningStyle, meetingPreference].filter(Boolean).length > 0
                ? `${[socialCadence, planningStyle, meetingPreference].filter(Boolean).length} of 3 set`
                : undefined
            }
          >
            <div className="field">
              <label className="field-label">How often would you like to make plans?</label>
              <select
                className="field-input"
                value={socialCadence}
                onChange={(e) => setSocialCadence(e.target.value)}
              >
                {SOCIAL_CADENCES.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label className="field-label">Planning style</label>
              <select
                className="field-input"
                value={planningStyle}
                onChange={(e) => setPlanningStyle(e.target.value)}
              >
                {PLANNING_STYLES.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label className="field-label">Meeting preference</label>
              <select
                className="field-input"
                value={meetingPreference}
                onChange={(e) => setMeetingPreference(e.target.value)}
              >
                {MEETING_PREFERENCES.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <p className="section-hint">What kind of environment do you enjoy?</p>
            <MultiSelectChips
              options={SOCIAL_ENVIRONMENTS}
              selectedValues={socialEnvironment}
              onToggle={toggleSocialEnvironment}
            />
          </CollapsibleSection>

          <CollapsibleSection
            title="Your City"
            defaultOpen
            summary={CITY_CIRCLE_STATUSES.find((o) => o.value === cityCircleStatus)?.label}
          >
            <div className="field">
              <label className="field-label">Where are you at socially in the city?</label>
              <select
                className="field-input"
                value={cityCircleStatus}
                onChange={(e) => setCityCircleStatus(e.target.value)}
              >
                {CITY_CIRCLE_STATUSES.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label className="field-label">Spending preference</label>
              <select
                className="field-input"
                value={spendingPreference}
                onChange={(e) => setSpendingPreference(e.target.value)}
              >
                {SPENDING_PREFERENCES.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
            <label className="privacy-toggle">
              <input
                type="checkbox"
                checked={comfortableWithDogs}
                onChange={(e) => setComfortableWithDogs(e.target.checked)}
              />
              I'm comfortable around dogs
            </label>
          </CollapsibleSection>

          <CollapsibleSection
            title="What are you hoping to find?"
            defaultOpen
            summary={socialGoals.length > 0 ? `${socialGoals.length} selected` : undefined}
          >
            <MultiSelectChips
              options={SOCIAL_GOALS}
              selectedValues={socialGoals}
              onToggle={toggleSocialGoal}
            />
            <div style={{ marginTop: "1.5rem" }}>
              <PrivacyToggles
                visibleOnProfile={visibleOnProfile}
                usableForMatching={usableForMatching}
                onChangeVisible={setVisibleOnProfile}
                onChangeMatching={setUsableForMatching}
              />
            </div>
          </CollapsibleSection>

          <div className="actions">
            <button type="button" className="cta" disabled={saving} onClick={handleSave}>
              {saving ? "Saving…" : "Finish"}
            </button>
            <button type="button" className="skip" onClick={finishOnboarding}>
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
