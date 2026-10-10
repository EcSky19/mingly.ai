import Head from "next/head";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import OnboardingStyles from "../components/OnboardingStyles";
import AppNav from "../components/AppNav";
import ReportBlockDialog from "../components/ReportBlockDialog";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type MatchItem = { name: string; loved: boolean };
type Match = {
  id: string;
  first_name: string;
  photo_url?: string | null;
  headline?: string | null;
  activities: MatchItem[];
  interests: MatchItem[];
  matched_at?: string | null;
  contact: { linkedin_url?: string | null; phone?: string | null; instagram?: string | null };
};

function resolveUrl(url: string): string {
  return /^https?:\/\//.test(url) ? url : `${API_URL}${url}`;
}

function matchedWhen(iso?: string | null): string {
  if (!iso) return "Matched recently";
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  if (days <= 0) return "Matched today";
  if (days === 1) return "Matched yesterday";
  return `Matched ${days} days ago`;
}

// Everyone you've matched with - where you've both said you're
// chosen Connect - and how to reach them, if they chose to share it.
export default function Matches() {
  const router = useRouter();
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [matches, setMatches] = useState<Match[]>([]);
  const [unmatchError, setUnmatchError] = useState("");
  const [reportTarget, setReportTarget] = useState<{ id: string; first_name: string } | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/auth/me`, { credentials: "include" })
      .then((res) => {
        if (!res.ok) router.replace("/");
      })
      .finally(() => setCheckingAuth(false));
  }, [router]);

  useEffect(() => {
    if (checkingAuth) return;
    fetch(`${API_URL}/api/matches`, { credentials: "include" })
      .then((res) => {
        if (!res.ok) throw new Error();
        return res.json();
      })
      .then(setMatches)
      .catch(() => setLoadError("Couldn't load your matches right now. Try refreshing the page."))
      .finally(() => setLoading(false));
  }, [checkingAuth]);

  function removeBlocked(id: string) {
    setMatches((prev) => prev.filter((m) => m.id !== id));
  }

  async function unmatch(match: Match) {
    if (!window.confirm(`Unmatch with ${match.first_name}? You'll both lose each other's contact info and your conversation will close. This can't be undone.`)) {
      return;
    }
    setUnmatchError("");
    try {
      const res = await fetch(`${API_URL}/api/matches/${match.id}`, { method: "DELETE", credentials: "include" });
      if (!res.ok && res.status !== 404) throw new Error();
      setMatches((prev) => prev.filter((m) => m.id !== match.id));
    } catch {
      setUnmatchError("Couldn't unmatch - please try again.");
    }
  }

  return (
    <>
      <Head>
        <title>Matches — Mingly.ai</title>
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

          <h1 className="headline">Your Matches</h1>
          <p className="subhead">People who said yes right back. Reach out and make a plan.</p>

          {(checkingAuth || loading) && <p className="section-hint">Loading your matches…</p>}
          {!checkingAuth && !loading && loadError && <p className="section-hint">{loadError}</p>}
          {unmatchError && <p className="section-hint" style={{ color: "#f472b6" }}>{unmatchError}</p>}

          {!checkingAuth && !loading && !loadError && matches.length === 0 && (
            <div className="discover-card discover-empty">
              <h2 className="discover-name">No matches yet</h2>
              <p>
                When someone you want to connect with wants to connect with you too, they'll show up here -
                along with how to reach them, if they've shared it.
              </p>
              <button type="button" className="cta" onClick={() => router.push("/home")}>
                Discover people
              </button>
            </div>
          )}

          {matches.length > 0 && (
            <div className="matches-grid">
              {matches.map((m) => {
                const hasContact = m.contact.linkedin_url || m.contact.phone || m.contact.instagram;
                const loved = [...m.activities, ...m.interests].filter((i) => i.loved).slice(0, 6);
                return (
                  <div className="match-card" key={m.id}>
                    <div className="match-header">
                      {m.photo_url ? (
                        <img src={resolveUrl(m.photo_url)} alt="" className="match-avatar" />
                      ) : (
                        <div className="match-avatar-placeholder">{m.first_name.charAt(0)}</div>
                      )}
                      <div>
                        <h2 className="match-name">{m.first_name}</h2>
                        {m.headline && <p className="discover-headline">{m.headline}</p>}
                        <p className="match-meta">{matchedWhen(m.matched_at)}</p>
                      </div>
                    </div>

                    {loved.length > 0 && (
                      <div className="profile-chip-row" style={{ marginTop: "1rem" }}>
                        {loved.map((item) => (
                          <span key={item.name} className="profile-chip profile-chip-loved">
                            {item.name}
                            <span className="profile-chip-icon-heart">♥</span>
                          </span>
                        ))}
                      </div>
                    )}

                    <button type="button" className="cta match-message-btn" onClick={() => router.push(`/messages/${m.id}`)}>
                      Message {m.first_name}
                    </button>

                    <div className="match-contact">
                      {hasContact ? (
                        <>
                          {m.contact.linkedin_url && (
                            <div className="match-contact-row">
                              <span className="match-contact-label">LinkedIn</span>
                              <a href={m.contact.linkedin_url} target="_blank" rel="noopener noreferrer">
                                View LinkedIn profile
                              </a>
                            </div>
                          )}
                          {m.contact.phone && (
                            <div className="match-contact-row">
                              <span className="match-contact-label">Phone</span>
                              <a href={`tel:${m.contact.phone.replace(/[^0-9+]/g, "")}`}>{m.contact.phone}</a>
                            </div>
                          )}
                          {m.contact.instagram && (
                            <div className="match-contact-row">
                              <span className="match-contact-label">Instagram</span>
                              <a href={`https://instagram.com/${m.contact.instagram}`} target="_blank" rel="noopener noreferrer">
                                @{m.contact.instagram}
                              </a>
                            </div>
                          )}
                        </>
                      ) : (
                        <p className="match-contact-none">
                          {m.first_name} hasn't shared other contact info - message them here on Mingly. You can
                          add yours on your profile whenever you're ready.
                        </p>
                      )}
                    </div>

                    <button type="button" className="match-unmatch" onClick={() => unmatch(m)}>
                      Unmatch
                    </button>
                    <button type="button" className="report-link" onClick={() => setReportTarget(m)}>
                      Report or block
                    </button>
                  </div>
                );
              })}
            </div>
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
