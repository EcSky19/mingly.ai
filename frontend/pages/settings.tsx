import Head from "next/head";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import OnboardingStyles from "../components/OnboardingStyles";
import AppNav from "../components/AppNav";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Me = { first_name: string; last_name: string; email: string };
type BlockedPerson = { id: string; first_name: string; photo_url?: string | null };

function resolveUrl(url: string): string {
  return /^https?:\/\//.test(url) ? url : `${API_URL}${url}`;
}

// Settings: account, privacy, blocked people, community guidelines, and
// account deletion - everything about your account in one place.
export default function Settings() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [showAsMutual, setShowAsMutual] = useState<boolean | null>(null);
  const [blocked, setBlocked] = useState<BlockedPerson[] | null>(null);
  const [confirmText, setConfirmText] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_URL}/api/auth/me`, { credentials: "include" })
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then(setMe)
      .catch(() => router.replace("/"));
  }, [router]);

  useEffect(() => {
    if (!me) return;
    fetch(`${API_URL}/api/circle`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setShowAsMutual(d.show_as_mutual_connection))
      .catch(() => {});
    loadBlocked();
  }, [me]);

  function loadBlocked() {
    fetch(`${API_URL}/api/blocks`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setBlocked)
      .catch(() => setError("Couldn't load your blocked list. Try refreshing the page."));
  }

  async function toggleMutual(value: boolean) {
    setShowAsMutual(value);
    const res = await fetch(`${API_URL}/api/circle/settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ show_as_mutual_connection: value }),
    }).catch(() => null);
    if (!res || !res.ok) {
      setShowAsMutual(!value);
      setError("Couldn't save that setting - please try again.");
    }
  }

  async function unblock(person: BlockedPerson) {
    if (!window.confirm(`Unblock ${person.first_name}? They won't be added back to your matches or circle automatically.`)) return;
    const res = await fetch(`${API_URL}/api/blocks/${person.id}`, { method: "DELETE", credentials: "include" }).catch(() => null);
    if (!res || (!res.ok && res.status !== 404)) setError("Couldn't unblock - please try again.");
    loadBlocked();
  }

  async function logout() {
    try {
      await fetch(`${API_URL}/api/auth/logout`, { method: "POST", credentials: "include" });
    } catch {
      // Fails open - worst case they see the sign-in page next visit anyway.
    }
    router.push("/");
  }

  async function deleteAccount() {
    setDeleting(true);
    setError("");
    const res = await fetch(`${API_URL}/api/auth/account`, { method: "DELETE", credentials: "include" }).catch(() => null);
    if (res && res.ok) {
      router.push("/");
      return;
    }
    setDeleting(false);
    setError("Couldn't delete your account - please try again.");
  }

  return (
    <>
      <Head>
        <title>Settings — Mingly.ai</title>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Public+Sans:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </Head>
      <main className="page">
        <div className="profile-wrap">
          <AppNav />
          <h1 className="headline">Settings</h1>
          {error && <p className="section-hint" style={{ color: "#f472b6" }}>{error}</p>}

          <div className="profile-columns">
            <div className="profile-col-left">
              <h2 className="circle-section-title">Account</h2>
              {me && (
                <div className="settings-row">
                  <div>
                    <p className="settings-strong">{me.first_name} {me.last_name}</p>
                    <p className="section-hint" style={{ margin: 0 }}>Signed in with LinkedIn · {me.email}</p>
                  </div>
                  <button type="button" className="discover-pass-btn" style={{ flex: "none" }} onClick={logout}>Log out</button>
                </div>
              )}

              <h2 className="circle-section-title">Privacy</h2>
              <p className="section-hint">
                Every detail on your profile has two separate switches: whether people can <strong>see</strong> it, and
                whether it can be <strong>used for matching</strong>. A detail can help your matches without ever being shown.
              </p>
              <div className="settings-links">
                <button type="button" className="edit-link" onClick={() => router.push("/onboarding")}>Personal info</button>
                <button type="button" className="edit-link" onClick={() => router.push("/onboarding/interests")}>Interests & activities</button>
                <button type="button" className="edit-link" onClick={() => router.push("/onboarding/social")}>Lifestyle & social</button>
                <button type="button" className="edit-link" onClick={() => router.push("/profile")}>Photos, About You & how matches reach you</button>
              </div>
              {showAsMutual !== null && (
                <label className="circle-setting" style={{ marginTop: "1.5rem" }}>
                  <input type="checkbox" checked={showAsMutual} onChange={(e) => toggleMutual(e.target.checked)} />
                  <span>
                    Show me as a mutual friend
                    <p>
                      When on, people your friends meet on Mingly may see you named, like "You both know Maya." When off,
                      you still help your friends' matches - you just won't be named.
                    </p>
                  </span>
                </label>
              )}

              <h2 className="circle-section-title">Community guidelines</h2>
              <p className="section-hint">
                Mingly is for building your life outside of work. Professional conversation is welcome - but recruiting,
                asking for referrals, sales outreach, and unwanted romantic pressure aren't. If someone crosses the line,
                use <strong>Report or block</strong> on their card. They're never told who reported them.
              </p>
            </div>

            <div className="profile-col-right">
              <h2 className="circle-section-title">Blocked people</h2>
              {blocked === null ? (
                <p className="section-hint">Loading…</p>
              ) : blocked.length === 0 ? (
                <p className="section-hint">You haven't blocked anyone.</p>
              ) : (
                blocked.map((p) => (
                  <div className="settings-row" key={p.id}>
                    <div className="match-header">
                      {p.photo_url ? (
                        <img src={resolveUrl(p.photo_url)} alt="" className="match-avatar" style={{ width: 44, height: 44 }} />
                      ) : (
                        <div className="match-avatar-placeholder" style={{ width: 44, height: 44, fontSize: "1.1rem" }}>{p.first_name.charAt(0)}</div>
                      )}
                      <p className="settings-strong">{p.first_name}</p>
                    </div>
                    <button type="button" className="discover-pass-btn" style={{ flex: "none" }} onClick={() => unblock(p)}>Unblock</button>
                  </div>
                ))
              )}

              <h2 className="circle-section-title">Delete account</h2>
              <div className="settings-danger">
                <p className="section-hint" style={{ marginTop: 0 }}>
                  Permanently deletes your account and everything in it - profile, photos, matches, circle, and contact
                  info. This can't be undone.
                </p>
                <div className="field">
                  <label className="field-label">Type DELETE to confirm</label>
                  <input className="field-input" value={confirmText} onChange={(e) => setConfirmText(e.target.value)} autoComplete="off" />
                </div>
                <button type="button" className="settings-delete-btn" disabled={confirmText !== "DELETE" || deleting} onClick={deleteAccount}>
                  {deleting ? "Deleting…" : "Delete my account"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
      <OnboardingStyles />
    </>
  );
}
