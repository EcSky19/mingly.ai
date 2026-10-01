import Head from "next/head";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/router";
import OnboardingStyles from "../components/OnboardingStyles";
import PrivacyTag from "../components/PrivacyTag";
import PrivacyToggles from "../components/PrivacyToggles";
import MultiSelectChips from "../components/MultiSelectChips";
import CollapsibleSection from "../components/CollapsibleSection";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const MAX_PHOTOS = 4;

// Converts a snake_case enum value into a readable label, e.g.
// "mid_career" -> "Mid career". A reasonable general-purpose fallback
// rather than hand-duplicating every label map already defined on the
// various onboarding pages.
function humanize(value?: string | null): string {
  if (!value) return "";
  return value.charAt(0).toUpperCase() + value.slice(1).replace(/_/g, " ");
}

type Photo = {
  id: string;
  url: string;
  tagged_activity_id?: string | null;
  tagged_activity_name?: string | null;
  tagged_interest_id?: string | null;
  tagged_interest_name?: string | null;
};

type LovedOption = { id: string; name: string; kind: "activity" | "interest" };

type ProfessionalData = {
  current_role?: string | null;
  current_role_visible_on_profile: boolean;
  company?: string | null;
  company_visible_on_profile: boolean;
  industry?: string | null;
  industry_visible_on_profile: boolean;
  career_stage?: string | null;
  career_stage_visible_on_profile: boolean;
};

type EducationEntry = {
  id: string;
  school?: string | null;
  degree?: string | null;
  field_of_study?: string | null;
  graduation_year?: number | null;
  visible_on_profile: boolean;
};

type LanguageEntry = {
  id: string;
  language: string;
  proficiency?: string | null;
  visible_on_profile: boolean;
};

type LocationEntry = {
  id: string;
  city?: string | null;
  label?: string | null;
  is_primary: boolean;
};

type PetEntry = {
  id: string;
  pet_type: string;
  name?: string | null;
  size?: string | null;
  activity_level?: string | null;
  comfortable_with_other_dogs?: boolean | null;
  visible_on_profile: boolean;
};

type InterestEntry = { interest_id: string; name: string; is_top_pick: boolean; visible_on_profile: boolean };
type ActivityEntry = {
  activity_id: string;
  name: string;
  category: string;
  interest_strength?: string | null;
  desired_frequency?: string | null;
  is_top_pick: boolean;
  visible_on_profile: boolean;
};

type SocialData = {
  career_orientation?: string | null;
  career_qualities?: string[] | null;
  early_bird_night_owl?: string | null;
  activity_level?: string | null;
  drinking_preference?: string | null;
  going_out_frequency?: string | null;
  indoor_outdoor_preference?: string | null;
  weekday_weekend_preference?: string | null;
  social_cadence?: string | null;
  planning_style?: string | null;
  meeting_preference?: string | null;
  social_environment?: string[] | null;
  social_goals?: string[] | null;
  spending_preference?: string | null;
  city_circle_status?: string | null;
  comfortable_with_dogs?: boolean | null;
  gender_identity?: string | null;
  gender_identity_description?: string | null;
  gender_identity_visible_on_profile: boolean;
  mingle_preference?: string[] | null;
  age_range?: string | null;
  age_range_visible_on_profile: boolean;
  age_preference?: string[] | null;
  visible_on_profile: boolean;
};

const GENDER_IDENTITIES = [
  { value: "", label: "Select one" },
  { value: "woman", label: "Woman" },
  { value: "man", label: "Man" },
  { value: "non_binary", label: "Non-binary" },
  { value: "self_describe", label: "Self-describe" },
  { value: "prefer_not_to_say", label: "Prefer not to say" },
];

const MINGLE_OPTIONS = [
  { value: "women", label: "Women" },
  { value: "men", label: "Men" },
  { value: "non_binary", label: "Non-binary people" },
];

const AGE_RANGES = [
  { value: "", label: "Select one" },
  { value: "18_24", label: "18-24" },
  { value: "25_29", label: "25-29" },
  { value: "30_34", label: "30-34" },
  { value: "35_39", label: "35-39" },
  { value: "40_49", label: "40-49" },
  { value: "50_plus", label: "50+" },
  { value: "prefer_not_to_say", label: "Prefer not to say" },
];

const AGE_PREFERENCE_OPTIONS = [
  { value: "18_24", label: "18-24" },
  { value: "25_29", label: "25-29" },
  { value: "30_34", label: "30-34" },
  { value: "35_39", label: "35-39" },
  { value: "40_49", label: "40-49" },
  { value: "50_plus", label: "50+" },
];

// "My Profile" - a read-only view of everything collected during
// onboarding, plus the photo upload feature.
export default function Profile() {
  const router = useRouter();
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [firstName, setFirstName] = useState("");
  const [linkedinPhotoUrl, setLinkedinPhotoUrl] = useState("");

  const [photos, setPhotos] = useState<Photo[]>([]);
  const [viewingPhotoIndex, setViewingPhotoIndex] = useState<number | null>(null);
  const [lovedOptions, setLovedOptions] = useState<LovedOption[]>([]);
  const [selectedTag, setSelectedTag] = useState(""); // "" = prefer not to tag, else "activity:<id>" or "interest:<id>"
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [pendingPreviewUrl, setPendingPreviewUrl] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [professional, setProfessional] = useState<ProfessionalData | null>(null);
  const [education, setEducation] = useState<EducationEntry[]>([]);
  const [languages, setLanguages] = useState<LanguageEntry[]>([]);
  const [locations, setLocations] = useState<LocationEntry[]>([]);
  const [pets, setPets] = useState<PetEntry[]>([]);
  const [interests, setInterests] = useState<InterestEntry[]>([]);
  const [activities, setActivities] = useState<ActivityEntry[]>([]);
  const [social, setSocial] = useState<SocialData | null>(null);

  const [editingAboutYou, setEditingAboutYou] = useState(false);
  const [genderIdentity, setGenderIdentity] = useState("");
  const [genderIdentityDescription, setGenderIdentityDescription] = useState("");
  const [genderIdentityVisible, setGenderIdentityVisible] = useState(false);
  const [genderIdentityMatching, setGenderIdentityMatching] = useState(true);
  const [minglePreference, setMinglePreference] = useState<string[]>(["everyone"]);
  const [ageRange, setAgeRange] = useState("");
  const [ageRangeVisible, setAgeRangeVisible] = useState(false);
  const [ageRangeMatching, setAgeRangeMatching] = useState(true);
  const [agePreference, setAgePreference] = useState<string[]>(["everyone"]);
  const [savingAboutYou, setSavingAboutYou] = useState(false);
  const [aboutYouError, setAboutYouError] = useState("");

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
        if (data?.profile_photo_url) setLinkedinPhotoUrl(data.profile_photo_url);
      })
      .finally(() => setCheckingAuth(false));
  }, [router]);

  useEffect(() => {
    if (checkingAuth) return;

    fetch(`${API_URL}/api/profile/photos`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then(setPhotos)
      .catch(() => {});

    fetch(`${API_URL}/api/profile/activities`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((rows: ActivityEntry[]) => {
        setActivities(rows);
        const loved = rows
          .filter((r) => r.is_top_pick)
          .map((r) => ({ id: r.activity_id, name: r.name, kind: "activity" as const }));
        setLovedOptions((prev) => [...prev.filter((o) => o.kind !== "activity"), ...loved]);
      })
      .catch(() => {});

    fetch(`${API_URL}/api/profile/interests`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((rows: InterestEntry[]) => {
        setInterests(rows);
        const loved = rows
          .filter((r) => r.is_top_pick)
          .map((r) => ({ id: r.interest_id, name: r.name, kind: "interest" as const }));
        setLovedOptions((prev) => [...prev.filter((o) => o.kind !== "interest"), ...loved]);
      })
      .catch(() => {});

    fetch(`${API_URL}/api/profile/professional`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setProfessional(data))
      .catch(() => {});

    fetch(`${API_URL}/api/profile/education`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then(setEducation)
      .catch(() => {});

    fetch(`${API_URL}/api/profile/languages`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then(setLanguages)
      .catch(() => {});

    fetch(`${API_URL}/api/profile/locations`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then(setLocations)
      .catch(() => {});

    fetch(`${API_URL}/api/profile/pets`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then(setPets)
      .catch(() => {});

    fetch(`${API_URL}/api/profile/social`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data: SocialData | null) => {
        setSocial(data);
        if (data) {
          setGenderIdentity(data.gender_identity || "");
          setGenderIdentityDescription(data.gender_identity_description || "");
          setGenderIdentityVisible(data.gender_identity_visible_on_profile || false);
          if (data.mingle_preference && data.mingle_preference.length > 0) {
            setMinglePreference(data.mingle_preference);
          }
          setAgeRange(data.age_range || "");
          setAgeRangeVisible(data.age_range_visible_on_profile || false);
          if (data.age_preference && data.age_preference.length > 0) {
            setAgePreference(data.age_preference);
          }
        }
      })
      .catch(() => {});
  }, [checkingAuth]);

  async function handleLogout() {
    try {
      await fetch(`${API_URL}/api/auth/logout`, { method: "POST", credentials: "include" });
    } catch {
      // Fails open - clear the session cookie server-side attempt was
      // made; worst case the person just sees the login page again on
      // their next visit even if this particular request dropped.
    }
    router.push("/");
  }

  function openLightbox(index: number) {
    setViewingPhotoIndex(index);
  }

  function closeLightbox() {
    setViewingPhotoIndex(null);
  }

  function showNextPhoto() {
    setViewingPhotoIndex((prev) => (prev === null ? null : (prev + 1) % photos.length));
  }

  function showPrevPhoto() {
    setViewingPhotoIndex((prev) => (prev === null ? null : (prev - 1 + photos.length) % photos.length));
  }

  useEffect(() => {
    if (viewingPhotoIndex === null) return;
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") closeLightbox();
      if (e.key === "ArrowRight") showNextPhoto();
      if (e.key === "ArrowLeft") showPrevPhoto();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [viewingPhotoIndex, photos.length]);

  function handleFileSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadError("");
    // Just stage the file and show a preview - the actual upload only
    // happens once the person picks a tag (or explicitly skips) and
    // confirms, not immediately on file selection.
    setPendingFile(file);
    setPendingPreviewUrl(URL.createObjectURL(file));
  }

  function cancelPendingUpload() {
    if (pendingPreviewUrl) URL.revokeObjectURL(pendingPreviewUrl);
    setPendingFile(null);
    setPendingPreviewUrl("");
    setSelectedTag("");
    setUploadError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function confirmUpload() {
    if (!pendingFile) return;
    setUploadError("");
    setUploading(true);

    const formData = new FormData();
    formData.append("file", pendingFile);
    if (selectedTag.startsWith("activity:")) {
      formData.append("tagged_activity_id", selectedTag.replace("activity:", ""));
    } else if (selectedTag.startsWith("interest:")) {
      formData.append("tagged_interest_id", selectedTag.replace("interest:", ""));
    }

    try {
      const res = await fetch(`${API_URL}/api/profile/photos`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });
      if (res.ok) {
        const created: Photo = await res.json();
        setPhotos((prev) => [...prev, created]);
        if (pendingPreviewUrl) URL.revokeObjectURL(pendingPreviewUrl);
        setPendingFile(null);
        setPendingPreviewUrl("");
        setSelectedTag("");
      } else {
        const err = await res.json().catch(() => null);
        setUploadError(err?.detail || "Couldn't upload that photo.");
      }
    } catch {
      setUploadError("Couldn't upload that photo.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function removePhoto(id: string) {
    setPhotos((prev) => prev.filter((p) => p.id !== id));
    try {
      await fetch(`${API_URL}/api/profile/photos/${id}`, {
        method: "DELETE",
        credentials: "include",
      });
    } catch {
      // Fails open - photo stays removed from view; a stale row server-side
      // isn't harmful and the user can retry the delete if it matters.
    }
  }

  function toggleMingleOption(value: string) {
    setMinglePreference((prev) => {
      if (prev.includes(value)) return prev.filter((v) => v !== value);
      // "everyone" is mutually exclusive with specific groups - selecting
      // any specific group clears "everyone", and vice versa.
      const withoutEveryone = prev.filter((v) => v !== "everyone");
      return [...withoutEveryone, value];
    });
  }

  function selectEveryoneOnly() {
    setMinglePreference(["everyone"]);
  }

  function toggleAgePreference(value: string) {
    setAgePreference((prev) => {
      if (prev.includes(value)) return prev.filter((v) => v !== value);
      const withoutEveryone = prev.filter((v) => v !== "everyone");
      return [...withoutEveryone, value];
    });
  }

  function selectAnyAge() {
    setAgePreference(["everyone"]);
  }

  async function saveAboutYou() {
    setSavingAboutYou(true);
    setAboutYouError("");
    try {
      // /api/profile/social fully replaces the row - it was designed for
      // /onboarding/social, which always sends its complete local state.
      // Sending only the About You fields here would silently wipe out
      // everything else already saved (career orientation, lifestyle,
      // etc.), so the full previously-loaded `social` state is merged in
      // underneath the new About You values.
      const res = await fetch(`${API_URL}/api/profile/social`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          ...(social || {}),
          gender_identity: genderIdentity || undefined,
          gender_identity_description:
            genderIdentity === "self_describe" ? genderIdentityDescription || undefined : undefined,
          gender_identity_visible_on_profile: genderIdentityVisible,
          gender_identity_usable_for_matching: genderIdentityMatching,
          mingle_preference: minglePreference,
          age_range: ageRange || undefined,
          age_range_visible_on_profile: ageRangeVisible,
          age_range_usable_for_matching: ageRangeMatching,
          age_preference: agePreference,
        }),
      });
      if (res.ok) {
        const updated: SocialData = await res.json();
        setSocial(updated);
        setEditingAboutYou(false);
      } else {
        const err = await res.json().catch(() => null);
        setAboutYouError(err?.detail ? JSON.stringify(err.detail) : "Couldn't save that.");
      }
    } catch {
      setAboutYouError("Couldn't save that.");
    } finally {
      setSavingAboutYou(false);
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
        <title>My Profile — Mingly.ai</title>
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

          <button type="button" className="skip" onClick={handleLogout} style={{ float: "right" }}>
            Log out
          </button>

          <h1 className="headline">{firstName ? `${firstName}'s` : "My"} Profile</h1>
          <p className="subhead">Everything you've shared, in one place.</p>

          <div className="profile-columns">
          <div className="profile-col-left">

          <CollapsibleSection title="Photos" defaultOpen summary={`${photos.length} of ${MAX_PHOTOS} added`}>
            {linkedinPhotoUrl && (
              <div className="field">
                <label className="field-label">From LinkedIn</label>
                <img src={linkedinPhotoUrl} alt="" className="profile-linkedin-photo" />
              </div>
            )}

            <p className="section-hint">
              Add up to {MAX_PHOTOS} photos — tag one to an activity or interest you've loved to
              show it in action. {photos.length} of {MAX_PHOTOS} added.
            </p>

            <div className="photo-grid">
              {photos.map((photo, index) => (
                <div className="photo-slot" key={photo.id}>
                  <img
                    src={`${API_URL}${photo.url}`}
                    alt=""
                    className="photo-thumb"
                    onClick={() => openLightbox(index)}
                    style={{ cursor: "pointer" }}
                  />
                  {(photo.tagged_activity_name || photo.tagged_interest_name) && (
                    <span className="photo-tag-label">
                      {photo.tagged_activity_name || photo.tagged_interest_name}
                    </span>
                  )}
                  <button
                    type="button"
                    className="photo-remove-btn"
                    onClick={() => removePhoto(photo.id)}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>

            {photos.length < MAX_PHOTOS && (
              <>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelected}
                  disabled={uploading}
                  style={{ display: "none" }}
                />

                {!pendingFile && (
                  <button
                    type="button"
                    className="add-entry"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Upload Photo
                  </button>
                )}

                {pendingFile && (
                  <div className="pending-photo-upload">
                    <img src={pendingPreviewUrl} alt="" className="photo-thumb" />
                    <div className="field">
                      <label className="field-label">Tag this photo to</label>
                      <select
                        className="field-input"
                        value={selectedTag}
                        onChange={(e) => setSelectedTag(e.target.value)}
                        disabled={uploading}
                      >
                        <option value="">Prefer not to tag</option>
                        {lovedOptions.map((o) => (
                          <option key={`${o.kind}:${o.id}`} value={`${o.kind}:${o.id}`}>
                            {o.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="actions">
                      <button
                        type="button"
                        className="cta"
                        disabled={uploading}
                        onClick={confirmUpload}
                      >
                        {uploading ? "Uploading…" : "Upload photo"}
                      </button>
                      <button
                        type="button"
                        className="skip"
                        disabled={uploading}
                        onClick={cancelPendingUpload}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {uploadError && <p className="section-hint" style={{ color: "#f472b6" }}>{uploadError}</p>}
              </>
            )}
          </CollapsibleSection>

          <CollapsibleSection
            title="About You"
            summary={GENDER_IDENTITIES.find((g) => g.value === genderIdentity)?.label}
          >
            {!editingAboutYou ? (
              <>
                <button type="button" className="edit-link" onClick={() => setEditingAboutYou(true)}>
                  Edit
                </button>
                {genderIdentity ? (
                  <p className="profile-item">
                    <span className="profile-item-label">Gender identity:</span>{" "}
                    {genderIdentity === "self_describe"
                      ? genderIdentityDescription || "Self-described"
                      : GENDER_IDENTITIES.find((g) => g.value === genderIdentity)?.label}
                    <PrivacyTag visible={genderIdentityVisible} />
                  </p>
                ) : (
                  <p className="profile-empty-hint">Nothing added yet.</p>
                )}
                <p className="profile-item">
                  <span className="profile-item-label">Who you'd like to mingle with:</span>{" "}
                  {minglePreference.includes("everyone")
                    ? "Everyone"
                    : minglePreference.map((v) => MINGLE_OPTIONS.find((o) => o.value === v)?.label).join(", ")}
                </p>
                {ageRange && (
                  <p className="profile-item">
                    <span className="profile-item-label">Age range:</span>{" "}
                    {AGE_RANGES.find((a) => a.value === ageRange)?.label}
                    <PrivacyTag visible={ageRangeVisible} />
                  </p>
                )}
                <p className="profile-item">
                  <span className="profile-item-label">Age preference:</span>{" "}
                  {agePreference.includes("everyone")
                    ? "Any age"
                    : agePreference
                        .map((v) => AGE_PREFERENCE_OPTIONS.find((o) => o.value === v)?.label)
                        .join(", ")}
                </p>
              </>
            ) : (
              <>
                <div className="field">
                  <label className="field-label">Gender identity</label>
                  <select
                    className="field-input"
                    value={genderIdentity}
                    onChange={(e) => setGenderIdentity(e.target.value)}
                  >
                    {GENDER_IDENTITIES.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
                {genderIdentity === "self_describe" && (
                  <div className="field">
                    <label className="field-label">Describe your gender identity</label>
                    <input
                      className="field-input"
                      type="text"
                      value={genderIdentityDescription}
                      onChange={(e) => setGenderIdentityDescription(e.target.value)}
                    />
                  </div>
                )}
                <PrivacyToggles
                  visibleOnProfile={genderIdentityVisible}
                  usableForMatching={genderIdentityMatching}
                  onChangeVisible={setGenderIdentityVisible}
                  onChangeMatching={setGenderIdentityMatching}
                />

                <p className="section-hint" style={{ marginTop: "1.5rem" }}>
                  This helps us find people you'd feel most comfortable spending time with in a
                  group or activity setting. Choose as many as you'd like — most people select
                  Everyone. This is never shown to anyone; it's only ever used to help find your
                  matches.
                </p>
                <div className="chip-grid">
                  <button
                    type="button"
                    className={minglePreference.includes("everyone") ? "chip chip-liked" : "chip"}
                    onClick={selectEveryoneOnly}
                  >
                    Everyone
                  </button>
                  {MINGLE_OPTIONS.map((o) => (
                    <button
                      key={o.value}
                      type="button"
                      className={minglePreference.includes(o.value) ? "chip chip-liked" : "chip"}
                      onClick={() => toggleMingleOption(o.value)}
                    >
                      {o.label}
                    </button>
                  ))}
                </div>

                <div className="field" style={{ marginTop: "1.5rem" }}>
                  <label className="field-label">Age range</label>
                  <select
                    className="field-input"
                    value={ageRange}
                    onChange={(e) => setAgeRange(e.target.value)}
                  >
                    {AGE_RANGES.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
                <PrivacyToggles
                  visibleOnProfile={ageRangeVisible}
                  usableForMatching={ageRangeMatching}
                  onChangeVisible={setAgeRangeVisible}
                  onChangeMatching={setAgeRangeMatching}
                />

                <p className="section-hint" style={{ marginTop: "1.5rem" }}>
                  Who's the right age range to find compatible people in? Choose as many as you'd
                  like — this is also never shown to anyone.
                </p>
                <div className="chip-grid">
                  <button
                    type="button"
                    className={agePreference.includes("everyone") ? "chip chip-liked" : "chip"}
                    onClick={selectAnyAge}
                  >
                    Any age
                  </button>
                  {AGE_PREFERENCE_OPTIONS.map((o) => (
                    <button
                      key={o.value}
                      type="button"
                      className={agePreference.includes(o.value) ? "chip chip-liked" : "chip"}
                      onClick={() => toggleAgePreference(o.value)}
                    >
                      {o.label}
                    </button>
                  ))}
                </div>

                {aboutYouError && (
                  <p className="section-hint" style={{ color: "#f472b6" }}>{aboutYouError}</p>
                )}
                <div className="actions">
                  <button
                    type="button"
                    className="cta"
                    disabled={savingAboutYou}
                    onClick={saveAboutYou}
                  >
                    {savingAboutYou ? "Saving…" : "Save"}
                  </button>
                  <button
                    type="button"
                    className="skip"
                    onClick={() => setEditingAboutYou(false)}
                  >
                    Cancel
                  </button>
                </div>
              </>
            )}
          </CollapsibleSection>

          </div>
          <div className="profile-col-right">

          <CollapsibleSection
            title="Professional"
            summary={professional?.current_role || professional?.company || undefined}
          >
            <button type="button" className="edit-link" onClick={() => router.push("/onboarding")}>
              Edit
            </button>
            {professional &&
            (professional.current_role || professional.company || professional.industry || professional.career_stage) ? (
              <>
                {professional.current_role && (
                  <p className="profile-item">
                    <span className="profile-item-label">Role:</span> {professional.current_role}
                    <PrivacyTag visible={professional.current_role_visible_on_profile} />
                  </p>
                )}
                {professional.company && (
                  <p className="profile-item">
                    <span className="profile-item-label">Company:</span> {professional.company}
                    <PrivacyTag visible={professional.company_visible_on_profile} />
                  </p>
                )}
                {professional.industry && (
                  <p className="profile-item">
                    <span className="profile-item-label">Industry:</span> {professional.industry}
                    <PrivacyTag visible={professional.industry_visible_on_profile} />
                  </p>
                )}
                {professional.career_stage && (
                  <p className="profile-item">
                    <span className="profile-item-label">Career stage:</span>{" "}
                    {humanize(professional.career_stage)}
                    <PrivacyTag visible={professional.career_stage_visible_on_profile} />
                  </p>
                )}
              </>
            ) : (
              <p className="profile-empty-hint">Nothing added yet.</p>
            )}
          </CollapsibleSection>

          <CollapsibleSection
            title="Education"
            summary={education.length > 0 ? `${education.length} added` : undefined}
          >
            <button type="button" className="edit-link" onClick={() => router.push("/onboarding")}>
              Edit
            </button>
            {education.length > 0 ? (
              education.map((entry) => (
                <p className="profile-item" key={entry.id}>
                  {[entry.degree, entry.field_of_study, entry.school].filter(Boolean).join(", ") ||
                    "Entry"}
                  {entry.graduation_year && <> · {entry.graduation_year}</>}
                  <PrivacyTag visible={entry.visible_on_profile} />
                </p>
              ))
            ) : (
              <p className="profile-empty-hint">Nothing added yet.</p>
            )}
          </CollapsibleSection>

          <CollapsibleSection
            title="Languages"
            summary={languages.length > 0 ? `${languages.length} added` : undefined}
          >
            <button type="button" className="edit-link" onClick={() => router.push("/onboarding")}>
              Edit
            </button>
            {languages.length > 0 ? (
              languages.map((entry) => (
                <p className="profile-item" key={entry.id}>
                  {entry.language}
                  {entry.proficiency && <> — {humanize(entry.proficiency)}</>}
                  <PrivacyTag visible={entry.visible_on_profile} />
                </p>
              ))
            ) : (
              <p className="profile-empty-hint">Nothing added yet.</p>
            )}
          </CollapsibleSection>

          <CollapsibleSection
            title="Location"
            summary={locations.find((l) => l.is_primary)?.city || locations[0]?.city || undefined}
          >
            <button type="button" className="edit-link" onClick={() => router.push("/onboarding")}>
              Edit
            </button>
            {locations.length > 0 ? (
              locations.map((entry) => (
                <p className="profile-item" key={entry.id}>
                  {entry.city || "Unnamed location"}
                  {entry.label && <> ({entry.label})</>}
                  {entry.is_primary && <> · Primary</>}
                </p>
              ))
            ) : (
              <p className="profile-empty-hint">Nothing added yet.</p>
            )}
          </CollapsibleSection>

          <CollapsibleSection title="Pets" summary={pets.length > 0 ? `${pets.length} added` : undefined}>
            <button type="button" className="edit-link" onClick={() => router.push("/onboarding")}>
              Edit
            </button>
            {pets.length > 0 ? (
              pets.map((entry) => (
                <p className="profile-item" key={entry.id}>
                  {entry.name || humanize(entry.pet_type)} ({humanize(entry.pet_type)})
                  {entry.size && <> · {humanize(entry.size)}</>}
                  {entry.activity_level && <> · {humanize(entry.activity_level)} activity</>}
                  <PrivacyTag visible={entry.visible_on_profile} />
                </p>
              ))
            ) : (
              <p className="profile-empty-hint">Nothing added yet.</p>
            )}
          </CollapsibleSection>

          <CollapsibleSection
            title="Interests"
            summary={interests.length > 0 ? `${interests.length} selected` : undefined}
          >
            <button
              type="button"
              className="edit-link"
              onClick={() => router.push("/onboarding/interests")}
            >
              Edit
            </button>
            {interests.length > 0 ? (
              <div className="profile-chip-row">
                {interests.map((entry) => (
                  <span
                    key={entry.interest_id}
                    className={entry.is_top_pick ? "profile-chip profile-chip-loved" : "profile-chip"}
                  >
                    {entry.name}
                  </span>
                ))}
              </div>
            ) : (
              <p className="profile-empty-hint">Nothing added yet.</p>
            )}
          </CollapsibleSection>

          <CollapsibleSection
            title="Activities"
            summary={activities.length > 0 ? `${activities.length} selected` : undefined}
          >
            <button
              type="button"
              className="edit-link"
              onClick={() => router.push("/onboarding/interests")}
            >
              Edit
            </button>
            {activities.length > 0 ? (
              <div className="profile-chip-row">
                {activities.map((entry) => (
                  <span
                    key={entry.activity_id}
                    className={entry.is_top_pick ? "profile-chip profile-chip-loved" : "profile-chip"}
                  >
                    {entry.name}
                    {entry.is_top_pick && entry.desired_frequency && (
                      <> · {humanize(entry.desired_frequency)}</>
                    )}
                  </span>
                ))}
              </div>
            ) : (
              <p className="profile-empty-hint">Nothing added yet.</p>
            )}
          </CollapsibleSection>

          <CollapsibleSection
            title="Lifestyle & Social"
            summary={social?.career_orientation ? humanize(social.career_orientation) : undefined}
          >
            <button
              type="button"
              className="edit-link"
              onClick={() => router.push("/onboarding/social")}
            >
              Edit
            </button>
            {social && <PrivacyTag visible={social.visible_on_profile} />}
            {social &&
            (social.career_orientation ||
              social.early_bird_night_owl ||
              social.activity_level ||
              social.social_cadence ||
              (social.social_goals && social.social_goals.length > 0)) ? (
              <>
                {social.career_orientation && (
                  <p className="profile-item">
                    <span className="profile-item-label">Career orientation:</span>{" "}
                    {humanize(social.career_orientation)}
                  </p>
                )}
                {social.career_qualities && social.career_qualities.length > 0 && (
                  <div className="profile-chip-row">
                    {social.career_qualities.map((q) => (
                      <span className="profile-chip" key={q}>
                        {humanize(q)}
                      </span>
                    ))}
                  </div>
                )}
                {social.early_bird_night_owl && (
                  <p className="profile-item">
                    <span className="profile-item-label">Early bird / night owl:</span>{" "}
                    {humanize(social.early_bird_night_owl)}
                  </p>
                )}
                {social.activity_level && (
                  <p className="profile-item">
                    <span className="profile-item-label">Activity level:</span>{" "}
                    {humanize(social.activity_level)}
                  </p>
                )}
                {social.drinking_preference && (
                  <p className="profile-item">
                    <span className="profile-item-label">Drinking:</span>{" "}
                    {humanize(social.drinking_preference)}
                  </p>
                )}
                {social.going_out_frequency && (
                  <p className="profile-item">
                    <span className="profile-item-label">Going out:</span>{" "}
                    {humanize(social.going_out_frequency)}
                  </p>
                )}
                {social.indoor_outdoor_preference && (
                  <p className="profile-item">
                    <span className="profile-item-label">Indoor / outdoor:</span>{" "}
                    {humanize(social.indoor_outdoor_preference)}
                  </p>
                )}
                {social.weekday_weekend_preference && (
                  <p className="profile-item">
                    <span className="profile-item-label">Weekdays / weekends:</span>{" "}
                    {humanize(social.weekday_weekend_preference)}
                  </p>
                )}
                {social.social_cadence && (
                  <p className="profile-item">
                    <span className="profile-item-label">How often they'd like to make plans:</span>{" "}
                    {humanize(social.social_cadence)}
                  </p>
                )}
                {social.planning_style && (
                  <p className="profile-item">
                    <span className="profile-item-label">Planning style:</span>{" "}
                    {humanize(social.planning_style)}
                  </p>
                )}
                {social.meeting_preference && (
                  <p className="profile-item">
                    <span className="profile-item-label">Meeting preference:</span>{" "}
                    {humanize(social.meeting_preference)}
                  </p>
                )}
                {social.social_environment && social.social_environment.length > 0 && (
                  <div className="profile-chip-row">
                    {social.social_environment.map((e) => (
                      <span className="profile-chip" key={e}>
                        {humanize(e)}
                      </span>
                    ))}
                  </div>
                )}
                {social.social_goals && social.social_goals.length > 0 && (
                  <div className="profile-chip-row">
                    {social.social_goals.map((g) => (
                      <span className="profile-chip" key={g}>
                        {humanize(g)}
                      </span>
                    ))}
                  </div>
                )}
                {social.spending_preference && (
                  <p className="profile-item">
                    <span className="profile-item-label">Spending preference:</span>{" "}
                    {humanize(social.spending_preference)}
                  </p>
                )}
                {social.city_circle_status && (
                  <p className="profile-item">
                    <span className="profile-item-label">City / circle status:</span>{" "}
                    {humanize(social.city_circle_status)}
                  </p>
                )}
                {social.comfortable_with_dogs && (
                  <p className="profile-item">Comfortable around dogs</p>
                )}
              </>
            ) : (
              <p className="profile-empty-hint">Nothing added yet.</p>
            )}
          </CollapsibleSection>

          </div>
          </div>
        </div>
      </main>

      {viewingPhotoIndex !== null && photos[viewingPhotoIndex] && (
        <div className="lightbox-overlay">
          <button type="button" className="lightbox-close" onClick={closeLightbox} aria-label="Close">
            ✕
          </button>
          {photos.length > 1 && (
            <button
              type="button"
              className="lightbox-arrow lightbox-arrow-left"
              onClick={showPrevPhoto}
              aria-label="Previous photo"
            >
              ‹
            </button>
          )}
          <img
            src={`${API_URL}${photos[viewingPhotoIndex].url}`}
            alt=""
            className="lightbox-image"
          />
          {photos.length > 1 && (
            <button
              type="button"
              className="lightbox-arrow lightbox-arrow-right"
              onClick={showNextPhoto}
              aria-label="Next photo"
            >
              ›
            </button>
          )}
        </div>
      )}

      <OnboardingStyles />
    </>
  );
}
