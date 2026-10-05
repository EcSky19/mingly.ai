import Head from "next/head";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import OnboardingStyles from "../components/OnboardingStyles";
import AppNav from "../components/AppNav";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type CandidatePhoto = { url: string; tag?: string | null };
type CandidateItem = { name: string; loved: boolean };
type Candidate = {
  id: string;
  first_name: string;
  intro: string;
  deferred?: boolean;
  photo_url?: string | null;
  headline?: string | null;
  photos: CandidatePhoto[];
  activities: CandidateItem[];
  interests: CandidateItem[];
};

// Photo URLs come back either relative (our own stored copies, served
// under /api/uploads) or, for not-yet-refreshed accounts, as LinkedIn's
// full legacy URL - only relative ones need the API origin prefixed.
function resolveUrl(url: string): string {
  return /^https?:\/\//.test(url) ? url : `${API_URL}${url}`;
}

function Chips({ items }: { items: CandidateItem[] }) {
  return (
    <div className="profile-chip-row">
      {items.map((item) => (
        <span key={item.name} className={item.loved ? "profile-chip profile-chip-loved" : "profile-chip"}>
          {item.name}
          <span className={item.loved ? "profile-chip-icon-heart" : "profile-chip-icon-check"}>
            {item.loved ? "♥" : "✓"}
          </span>
        </span>
      ))}
    </div>
  );
}

// Discovery: ranked candidates (eligibility + compatibility scoring on
// the backend), one at a time. Everything shown here has already been
// filtered server-side through each person's own visibility settings.
export default function Discover() {
  const router = useRouter();
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [queue, setQueue] = useState<Candidate[]>([]);
  const [total, setTotal] = useState(0);
  const [photoIndex, setPhotoIndex] = useState(0);
  const [acting, setActing] = useState(false);
  const [actionError, setActionError] = useState("");
  // Set when your "Interested" completes a mutual match - shown as its own
  // moment before moving on to the next person.
  const [justMatched, setJustMatched] = useState<Candidate | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/auth/me`, { credentials: "include" })
      .then((res) => {
        if (!res.ok) router.replace("/");
      })
      .finally(() => setCheckingAuth(false));
  }, [router]);

  useEffect(() => {
    if (checkingAuth) return;
    fetch(`${API_URL}/api/discover/candidates`, { credentials: "include" })
      .then((res) => {
        if (!res.ok) throw new Error();
        return res.json();
      })
      .then((rows: Candidate[]) => {
        setQueue(rows);
        setTotal(rows.length);
      })
      .catch(() => setLoadError("Couldn't load people right now. Try refreshing the page."))
      .finally(() => setLoading(false));
  }, [checkingAuth]);

  const current = queue[0];

  async function act(action: "interested" | "dismissed" | "later") {
    if (!current || acting) return;
    setActing(true);
    setActionError("");
    try {
      const res = await fetch(`${API_URL}/api/discover/interact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ target_user_id: current.id, action }),
      });
      if (!res.ok) throw new Error();
      const result: { matched?: boolean } = await res.json();
      if (action === "interested" && result.matched) setJustMatched(current);
      // Only advance once the server has recorded it, so a failed save
      // never silently skips someone.
      if (action === "later") {
        // Decide later: not a pass - they go to the back of the line and
        // come back after everyone else, marked as saved for later.
        setQueue((prev) => [...prev.slice(1), { ...prev[0], deferred: true }]);
      } else {
        setQueue((prev) => prev.slice(1));
      }
      setPhotoIndex(0);
    } catch {
      setActionError("Couldn't save that - please try again.");
    } finally {
      setActing(false);
    }
  }

  const allPhotos: CandidatePhoto[] = current
    ? [...(current.photo_url ? [{ url: current.photo_url, tag: null }] : []), ...current.photos]
    : [];
  const shownPhoto = allPhotos[Math.min(photoIndex, Math.max(allPhotos.length - 1, 0))];

  return (
    <>
      <Head>
        <title>Discover — Mingly.ai</title>
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

          <h1 className="headline">People you might click with</h1>
          <p className="subhead">Ranked by what you actually share - activities first.</p>

          {(checkingAuth || loading) && <p className="section-hint">Finding people for you…</p>}

          {!checkingAuth && !loading && loadError && <p className="section-hint">{loadError}</p>}

          {justMatched && (
            <div className="discover-card match-moment">
              <h2 className="match-moment-title">It's a match!</h2>
              <p>
                You and {justMatched.first_name} are both interested. Head to your matches to see how
                to reach them and make a plan.
              </p>
              <div className="match-moment-actions">
                <button type="button" className="cta" onClick={() => router.push("/matches")}>
                  See your matches
                </button>
                <button type="button" className="discover-pass-btn" style={{ flex: "none" }} onClick={() => setJustMatched(null)}>
                  Keep discovering
                </button>
              </div>
            </div>
          )}

          {!justMatched && !checkingAuth && !loading && !loadError && !current && (
            <div className="discover-card discover-empty">
              <h2 className="discover-name">
                {total === 0 ? "No one new to show right now" : "You're all caught up"}
              </h2>
              <p>
                {total === 0
                  ? "Mingly is just getting started near you - as more people join, they'll show up here. Adding more activities and interests to your profile helps us find people you'd click with."
                  : "You've seen everyone we have for you at the moment. New people will appear here as they join."}
              </p>
              <button type="button" className="cta" onClick={() => router.push("/profile")}>
                Go to my profile
              </button>
            </div>
          )}

          {!justMatched && !checkingAuth && !loading && current && (
            <>
              <p className="discover-counter">
                {total - queue.length + 1} of {total}
              </p>
              <div className="discover-card">
                <div className="discover-card-grid">
                  <div>
                    {shownPhoto ? (
                      <img src={resolveUrl(shownPhoto.url)} alt="" className="discover-main-photo" />
                    ) : (
                      <div className="discover-photo-placeholder">{current.first_name.charAt(0)}</div>
                    )}
                    {shownPhoto?.tag && <p className="discover-photo-tag">{shownPhoto.tag}</p>}
                    {allPhotos.length > 1 && (
                      <div className="discover-thumbs">
                        {allPhotos.map((p, i) => (
                          <img
                            key={p.url}
                            src={resolveUrl(p.url)}
                            alt=""
                            className={i === photoIndex ? "discover-thumb discover-thumb-active" : "discover-thumb"}
                            onClick={() => setPhotoIndex(i)}
                          />
                        ))}
                      </div>
                    )}
                  </div>

                  <div>
                    {current.deferred && <p className="discover-deferred-badge">You saved {current.first_name} for later</p>}
                    <h2 className="discover-name">{current.first_name}</h2>
                    {current.headline && <p className="discover-headline">{current.headline}</p>}

                    {current.intro && (
                      <>
                        <p className="discover-label">Why you two might click</p>
                        <p className="discover-intro">{current.intro}</p>
                      </>
                    )}

                    {current.activities.length > 0 && (
                      <>
                        <p className="discover-label">Activities</p>
                        <Chips items={current.activities} />
                      </>
                    )}

                    {current.interests.length > 0 && (
                      <>
                        <p className="discover-label">Interests</p>
                        <Chips items={current.interests} />
                      </>
                    )}

                    <div className="discover-actions">
                      <button
                        type="button"
                        className="discover-pass-btn"
                        disabled={acting}
                        onClick={() => act("dismissed")}
                      >
                        Pass
                      </button>
                      <button
                        type="button"
                        className="discover-pass-btn discover-later-btn"
                        disabled={acting}
                        onClick={() => act("later")}
                      >
                        Decide later
                      </button>
                      <button type="button" className="cta" disabled={acting} onClick={() => act("interested")}>
                        Interested
                      </button>
                    </div>
                    {actionError && (
                      <p className="section-hint" style={{ color: "#f472b6" }}>
                        {actionError}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </main>
      <OnboardingStyles />
    </>
  );
}
