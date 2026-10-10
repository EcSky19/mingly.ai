import Head from "next/head";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import OnboardingStyles from "../../components/OnboardingStyles";
import AppNav from "../../components/AppNav";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Conversation = {
  person: { id: string; first_name: string; photo_url?: string | null; headline?: string | null };
  relationship: "match" | "circle";
  last_message: { body: string; from_me: boolean; created_at: string };
  unread: number;
};

function resolveUrl(url: string): string {
  return /^https?:\/\//.test(url) ? url : `${API_URL}${url}`;
}

function shortTime(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  if (d.toDateString() === now.toDateString()) return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  const days = Math.floor((now.getTime() - d.getTime()) / 86_400_000);
  if (days < 7) return d.toLocaleDateString([], { weekday: "short" });
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

// Your conversations with matches and circle members, newest first.
export default function Messages() {
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    function load() {
      fetch(`${API_URL}/api/messages`, { credentials: "include" })
        .then((r) => {
          if (r.status === 401) router.replace("/");
          return r.ok ? r.json() : Promise.reject();
        })
        .then((d) => !cancelled && (setConversations(d), setError("")))
        .catch(() => !cancelled && setError("Couldn't load your messages. Try refreshing the page."));
    }
    load();
    const timer = setInterval(() => document.visibilityState === "visible" && load(), 15000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [router]);

  return (
    <>
      <Head>
        <title>Messages — Mingly.ai</title>
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
          <h1 className="headline">Messages</h1>
          <p className="subhead">Talk with your matches and your circle here - no need to share your number until you want to.</p>
          {error && <p className="section-hint" style={{ color: "#f472b6" }}>{error}</p>}
          {conversations === null && !error && <p className="section-hint">Loading…</p>}
          {conversations && conversations.length === 0 && (
            <div className="match-card" style={{ maxWidth: 560 }}>
              <p className="section-hint" style={{ marginTop: 0 }}>
                No conversations yet. Say hi to one of your matches or someone in your circle.
              </p>
              <div className="dialog-actions" style={{ justifyContent: "flex-start" }}>
                <button type="button" className="cta" onClick={() => router.push("/matches")}>Go to Matches</button>
                <button type="button" className="discover-pass-btn" style={{ flex: "none" }} onClick={() => router.push("/circle")}>My Circle</button>
              </div>
            </div>
          )}
          {conversations && conversations.length > 0 && (
            <ul className="inbox">
              {conversations.map((c) => (
                <li key={c.person.id}>
                  <button type="button" className={c.unread ? "inbox-row inbox-row-unread" : "inbox-row"} onClick={() => router.push(`/messages/${c.person.id}`)}>
                    {c.person.photo_url ? (
                      <img src={resolveUrl(c.person.photo_url)} alt="" className="inbox-avatar" />
                    ) : (
                      <span className="inbox-avatar inbox-avatar-placeholder">{c.person.first_name.charAt(0)}</span>
                    )}
                    <span className="inbox-text">
                      <span className="inbox-top">
                        <span className="inbox-name">{c.person.first_name}</span>
                        <span className="inbox-tag">{c.relationship === "circle" ? "Circle" : "Match"}</span>
                        <span className="inbox-time">{shortTime(c.last_message.created_at)}</span>
                      </span>
                      <span className="inbox-preview">
                        {c.last_message.from_me ? "You: " : ""}
                        {c.last_message.body}
                      </span>
                    </span>
                    {c.unread > 0 && <span className="inbox-badge" aria-label={`${c.unread} unread`}>{c.unread}</span>}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>
      <OnboardingStyles />
    </>
  );
}
