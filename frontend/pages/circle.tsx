import Head from "next/head";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import OnboardingStyles from "../components/OnboardingStyles";
import AppNav from "../components/AppNav";
import ReportBlockDialog from "../components/ReportBlockDialog";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Person = { id: string; first_name: string; photo_url?: string | null; headline?: string | null };
type CircleRequest = { id: string; from_user: Person };
type CircleData = { members: Person[]; requests: CircleRequest[]; show_as_mutual_connection: boolean };

function resolveUrl(url: string): string {
  return /^https?:\/\//.test(url) ? url : `${API_URL}${url}`;
}

function Avatar({ person }: { person: Person }) {
  return person.photo_url ? (
    <img src={resolveUrl(person.photo_url)} alt="" className="match-avatar" />
  ) : (
    <div className="match-avatar-placeholder">{person.first_name.charAt(0)}</div>
  );
}

// My Circle: the people you trust. Invite friends with your personal link;
// once they join and accept, you're in each other's circle - and their
// friends become warm introductions in Discovery.
export default function Circle() {
  const router = useRouter();
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [data, setData] = useState<CircleData | null>(null);
  const [inviteUrl, setInviteUrl] = useState("");
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [reportTarget, setReportTarget] = useState<{ id: string; first_name: string } | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/auth/me`, { credentials: "include" })
      .then((res) => {
        if (!res.ok) router.replace("/");
      })
      .finally(() => setCheckingAuth(false));
  }, [router]);

  function load() {
    fetch(`${API_URL}/api/circle`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setData)
      .catch(() => setError("Couldn't load your circle right now. Try refreshing the page."));
  }

  useEffect(() => {
    if (checkingAuth) return;
    load();
    fetch(`${API_URL}/api/circle/invite-link`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setInviteUrl(d.url))
      .catch(() => {});
  }, [checkingAuth]);

  const shareMessage = `I'm on Mingly.ai, meeting people who are into the same things. Join me and we'll be in each other's circle: ${inviteUrl}`;

  async function share() {
    // The person sends the invite themselves, from their own phone or app -
    // Mingly never messages anyone's contacts on their behalf.
    if (typeof navigator !== "undefined" && navigator.share) {
      try {
        await navigator.share({ title: "Join me on Mingly.ai", text: shareMessage });
        return;
      } catch {
        // They closed the share sheet - nothing to do.
        return;
      }
    }
    copy(shareMessage);
  }

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Couldn't copy - you can select the link and copy it manually.");
    }
  }

  async function answer(req: CircleRequest, action: "accept" | "decline") {
    setError("");
    const res = await fetch(`${API_URL}/api/circle/requests/${req.id}/${action}`, { method: "POST", credentials: "include" }).catch(() => null);
    if (!res || !res.ok) setError("Couldn't save that - please try again.");
    load();
  }

  function removeBlocked(id: string) {
    setData((d) => (d ? { ...d, members: d.members.filter((m) => m.id !== id) } : d));
  }

  async function remove(person: Person) {
    if (!window.confirm(`Remove ${person.first_name} from your circle? You'll be removed from theirs too.`)) return;
    setError("");
    const res = await fetch(`${API_URL}/api/circle/members/${person.id}`, { method: "DELETE", credentials: "include" }).catch(() => null);
    if (!res || (!res.ok && res.status !== 404)) setError("Couldn't remove - please try again.");
    load();
  }

  async function toggleMutual(value: boolean) {
    setData((d) => (d ? { ...d, show_as_mutual_connection: value } : d));
    const res = await fetch(`${API_URL}/api/circle/settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ show_as_mutual_connection: value }),
    }).catch(() => null);
    if (!res || !res.ok) {
      setError("Couldn't save that setting - please try again.");
      load();
    }
  }

  return (
    <>
      <Head>
        <title>My Circle — Mingly.ai</title>
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

          <h1 className="headline">My Circle</h1>
          <p className="subhead">
            The people you trust. Their friends become warm introductions in Discover - "You both know Maya."
          </p>

          <div className="circle-invite-box">
            <p className="discover-label" style={{ marginTop: 0 }}>Invite your friends</p>
            <p className="section-hint" style={{ margin: 0 }}>
              Anyone who joins through your link can add you to their circle in one tap.
            </p>
            <div className="circle-link-row">
              <input className="field-input" readOnly value={inviteUrl} onFocus={(e) => e.target.select()} />
              <button type="button" className="discover-pass-btn" style={{ flex: "none" }} disabled={!inviteUrl} onClick={() => copy(inviteUrl)}>
                {copied ? "Copied!" : "Copy link"}
              </button>
              <button type="button" className="cta" disabled={!inviteUrl} onClick={share}>
                Share
              </button>
            </div>
          </div>

          {error && <p className="section-hint" style={{ color: "#f472b6" }}>{error}</p>}
          {!data && !error && <p className="section-hint">Loading your circle…</p>}

          {data && data.requests.length > 0 && (
            <>
              <h2 className="circle-section-title">Waiting for you</h2>
              <div className="matches-grid">
                {data.requests.map((req) => (
                  <div className="match-card" key={req.id}>
                    <div className="match-header">
                      <Avatar person={req.from_user} />
                      <div>
                        <h3 className="match-name">{req.from_user.first_name}</h3>
                        {req.from_user.headline && <p className="discover-headline">{req.from_user.headline}</p>}
                        <p className="match-meta">Invited you to Mingly</p>
                      </div>
                    </div>
                    <div className="circle-person-actions">
                      <button type="button" className="discover-pass-btn" onClick={() => answer(req, "decline")}>
                        Not now
                      </button>
                      <button type="button" className="cta" style={{ flex: 1 }} onClick={() => answer(req, "accept")}>
                        Add to my circle
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {data && (
            <>
              <h2 className="circle-section-title">
                Your circle{data.members.length > 0 ? ` (${data.members.length})` : ""}
              </h2>
              {data.members.length === 0 ? (
                <p className="section-hint">
                  No one yet. Share your invite link with a few friends - when they join, they'll show up here.
                </p>
              ) : (
                <div className="matches-grid">
                  {data.members.map((m) => (
                    <div className="match-card" key={m.id}>
                      <div className="match-header">
                        <Avatar person={m} />
                        <div>
                          <h3 className="match-name">{m.first_name}</h3>
                          {m.headline && <p className="discover-headline">{m.headline}</p>}
                        </div>
                      </div>
                      <button type="button" className="match-unmatch" onClick={() => remove(m)}>
                        Remove from circle
                      </button>
                      <button type="button" className="report-link" onClick={() => setReportTarget(m)}>
                        Report or block
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <label className="circle-setting">
                <input
                  type="checkbox"
                  checked={data.show_as_mutual_connection}
                  onChange={(e) => toggleMutual(e.target.checked)}
                />
                <span>
                  Show me as a mutual friend
                  <p>
                    When on, people your friends meet on Mingly may see you named, like "You both know Maya." When
                    off, you still help your friends' matches - you just won't be named.
                  </p>
                </span>
              </label>
            </>
          )}
        </div>
      </main>
      {reportTarget && (
        <ReportBlockDialog
          userId={reportTarget.id}
          firstName={reportTarget.first_name}
          onClose={() => setReportTarget(null)}
          onBlocked={() => removeBlocked(reportTarget.id)}
        />
      )}
      <OnboardingStyles />
    </>
  );
}
