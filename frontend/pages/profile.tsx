import Head from "next/head";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/router";
import OnboardingStyles from "../components/OnboardingStyles";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const MAX_PHOTOS = 4;

type Photo = {
  id: string;
  url: string;
  tagged_activity_id?: string | null;
  tagged_activity_name?: string | null;
  tagged_interest_id?: string | null;
  tagged_interest_name?: string | null;
};

type LovedOption = { id: string; name: string; kind: "activity" | "interest" };

// "My Profile" - a read-only view of everything collected during
// onboarding, plus the photo upload feature. This first version covers
// the LinkedIn photo + up to 4 additional tagged photos; the full
// data-aggregation sections (professional, education, etc.) are a
// separate, larger follow-up piece.
export default function Profile() {
  const router = useRouter();
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [firstName, setFirstName] = useState("");
  const [linkedinPhotoUrl, setLinkedinPhotoUrl] = useState("");

  const [photos, setPhotos] = useState<Photo[]>([]);
  const [lovedOptions, setLovedOptions] = useState<LovedOption[]>([]);
  const [selectedTag, setSelectedTag] = useState(""); // "" = prefer not to tag, else "activity:<id>" or "interest:<id>"
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [pendingPreviewUrl, setPendingPreviewUrl] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

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
      .then((rows: { activity_id: string; name: string; is_top_pick: boolean }[]) => {
        const loved = rows
          .filter((r) => r.is_top_pick)
          .map((r) => ({ id: r.activity_id, name: r.name, kind: "activity" as const }));
        setLovedOptions((prev) => [...prev.filter((o) => o.kind !== "activity"), ...loved]);
      })
      .catch(() => {});

    fetch(`${API_URL}/api/profile/interests`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : []))
      .then((rows: { interest_id: string; name: string; is_top_pick: boolean }[]) => {
        const loved = rows
          .filter((r) => r.is_top_pick)
          .map((r) => ({ id: r.interest_id, name: r.name, kind: "interest" as const }));
        setLovedOptions((prev) => [...prev.filter((o) => o.kind !== "interest"), ...loved]);
      })
      .catch(() => {});
  }, [checkingAuth]);

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
        <div className="wrap">
          <span className="wordmark">
            <img src="/mingly-mark.png" alt="" className="mark" />
            <span>Mingly.ai</span>
          </span>

          <h1 className="headline">{firstName ? `${firstName}'s` : "My"} Profile</h1>
          <p className="subhead">Everything you've shared, in one place.</p>

          <section className="section">
            <h2 className="section-title">Photos</h2>
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
              {photos.map((photo) => (
                <div className="photo-slot" key={photo.id}>
                  <img src={`${API_URL}${photo.url}`} alt="" className="photo-thumb" />
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
                    + Choose a photo
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
          </section>
        </div>
      </main>
      <OnboardingStyles />
    </>
  );
}
