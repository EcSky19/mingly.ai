import Head from "next/head";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/router";
import OnboardingStyles from "../../components/OnboardingStyles";
import AppNav from "../../components/AppNav";
import ReportBlockDialog from "../../components/ReportBlockDialog";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const MAX_LENGTH = 2000;

type Message = { id: string; from_me: boolean; body: string; created_at: string };
type Thread = {
  person: { id: string; first_name: string; photo_url?: string | null; headline?: string | null };
  relationship: "match" | "circle";
  messages: Message[];
  has_more: boolean;
};

function resolveUrl(url: string): string {
  return /^https?:\/\//.test(url) ? url : `${API_URL}${url}`;
}

function dayLabel(iso: string): string {
  const d = new Date(iso);
  const today = new Date();
  const yesterday = new Date(today.getTime() - 86_400_000);
  if (d.toDateString() === today.toDateString()) return "Today";
  if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
  return d.toLocaleDateString([], { weekday: "long", month: "short", day: "numeric" });
}

// One conversation. New messages arrive by checking every few seconds while
// the page is open and visible - simple, and quick enough for the beta.
export default function Conversation() {
  const router = useRouter();
  const userId = typeof router.query.userId === "string" ? router.query.userId : "";
  const [thread, setThread] = useState<Thread | null>(null);
  const [closed, setClosed] = useState(false);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [reportOpen, setReportOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const stickToBottom = useRef(true);

  const load = useCallback(async () => {
    if (!userId) return;
    const res = await fetch(`${API_URL}/api/messages/with/${encodeURIComponent(userId)}`, { credentials: "include" }).catch(() => null);
    if (!res) return;
    if (res.status === 401) return void router.replace("/");
    if (res.status === 404) return void setClosed(true);
    if (!res.ok) return;
    const latest: Thread = await res.json();
    setThread((prev) => {
      if (!prev) return latest;
      // Keep any older pages already loaded; replace the newest page.
      const ids = new Set(latest.messages.map((m) => m.id));
      const older = prev.messages.filter((m) => !ids.has(m.id) && (!latest.messages[0] || m.created_at < latest.messages[0].created_at));
      return { ...latest, messages: [...older, ...latest.messages], has_more: older.length ? prev.has_more : latest.has_more };
    });
  }, [userId, router]);

  useEffect(() => {
    load();
    const timer = setInterval(() => document.visibilityState === "visible" && load(), 4000);
    return () => clearInterval(timer);
  }, [load]);

  const count = thread?.messages.length ?? 0;
  useEffect(() => {
    if (stickToBottom.current) bottomRef.current?.scrollIntoView({ block: "end" });
  }, [count]);

  useEffect(() => {
    const onScroll = () => {
      stickToBottom.current = window.innerHeight + window.scrollY >= document.body.scrollHeight - 120;
    };
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  async function loadOlder() {
    if (!thread?.messages.length) return;
    setLoadingOlder(true);
    stickToBottom.current = false;
    const res = await fetch(
      `${API_URL}/api/messages/with/${encodeURIComponent(userId)}?before=${thread.messages[0].id}`,
      { credentials: "include" },
    ).catch(() => null);
    setLoadingOlder(false);
    if (!res || !res.ok) return;
    const older: Thread = await res.json();
    setThread((prev) => (prev ? { ...prev, messages: [...older.messages, ...prev.messages], has_more: older.has_more } : prev));
  }

  async function send() {
    const body = draft.trim();
    if (!body || sending) return;
    setSending(true);
    setError("");
    const res = await fetch(`${API_URL}/api/messages/with/${encodeURIComponent(userId)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ body }),
    }).catch(() => null);
    setSending(false);
    if (res && res.status === 201) {
      const message: Message = await res.json();
      setDraft("");
      stickToBottom.current = true;
      setThread((prev) => (prev ? { ...prev, messages: [...prev.messages, message] } : prev));
      return;
    }
    if (res && res.status === 404) return void setClosed(true);
    if (res && res.status === 429) return void setError("You're sending messages too quickly - please wait a moment.");
    setError("Your message didn't send - please try again.");
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends; Shift+Enter adds a new line.
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      send();
    }
  }

  const name = thread?.person.first_name ?? "";
  let lastDay = "";

  return (
    <>
      <Head>
        <title>{name ? `${name} — Messages — Mingly.ai` : "Messages — Mingly.ai"}</title>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Public+Sans:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </Head>
      <main className="page">
        <div className="profile-wrap chat-wrap">
          <AppNav />
          <button type="button" className="back-link chat-back" onClick={() => router.push("/messages")}>← All messages</button>

          {closed ? (
            <div className="match-card" style={{ maxWidth: 560 }}>
              <h1 className="match-name" style={{ marginBottom: "0.5rem" }}>This conversation isn't available</h1>
              <p className="section-hint">
                You can message people you've matched with and people in your circle. If you unmatched or left each
                other's circle, the conversation closes for both of you.
              </p>
              <button type="button" className="cta" onClick={() => router.push("/messages")}>Back to Messages</button>
            </div>
          ) : !thread ? (
            <p className="section-hint">Loading…</p>
          ) : (
            <>
              <div className="chat-header">
                {thread.person.photo_url ? (
                  <img src={resolveUrl(thread.person.photo_url)} alt="" className="inbox-avatar" />
                ) : (
                  <span className="inbox-avatar inbox-avatar-placeholder">{name.charAt(0)}</span>
                )}
                <div className="chat-header-text">
                  <h1 className="match-name">{name}</h1>
                  <p className="match-meta">
                    {thread.relationship === "circle" ? "In your circle" : "Your match"}
                    {thread.person.headline ? ` · ${thread.person.headline}` : ""}
                  </p>
                </div>
                <button type="button" className="report-link chat-report" onClick={() => setReportOpen(true)}>Report or block</button>
              </div>

              <div className="chat-log" aria-live="polite">
                {thread.has_more && (
                  <button type="button" className="match-unmatch chat-older" disabled={loadingOlder} onClick={loadOlder}>
                    {loadingOlder ? "Loading…" : "Show earlier messages"}
                  </button>
                )}
                {thread.messages.length === 0 && (
                  <p className="chat-empty">
                    Say hi to {name}. Keep the conversation on Mingly until you're comfortable sharing more - and
                    for a first meetup, pick somewhere public.
                  </p>
                )}
                {thread.messages.map((m) => {
                  const day = dayLabel(m.created_at);
                  const showDay = day !== lastDay;
                  lastDay = day;
                  return (
                    <div key={m.id}>
                      {showDay && <p className="chat-day">{day}</p>}
                      <div className={m.from_me ? "chat-bubble chat-bubble-me" : "chat-bubble"}>
                        {m.body}
                        <span className="chat-time">{new Date(m.created_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}</span>
                      </div>
                    </div>
                  );
                })}
                <div ref={bottomRef} />
              </div>

              <div className="chat-composer">
                {error && <p className="section-hint" style={{ color: "#f472b6", margin: "0 0 0.5rem" }}>{error}</p>}
                <div className="chat-composer-row">
                  <textarea
                    className="field-input chat-input"
                    rows={2}
                    maxLength={MAX_LENGTH}
                    placeholder={`Message ${name}`}
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={onKeyDown}
                    aria-label={`Message ${name}`}
                  />
                  <button type="button" className="cta" disabled={!draft.trim() || sending} onClick={send}>
                    {sending ? "Sending…" : "Send"}
                  </button>
                </div>
                {draft.length > MAX_LENGTH - 200 && <p className="match-meta">{MAX_LENGTH - draft.length} characters left</p>}
              </div>
            </>
          )}
        </div>
      </main>
      {reportOpen && thread && (
        <ReportBlockDialog
          userId={thread.person.id}
          firstName={name}
          onClose={() => setReportOpen(false)}
          onBlocked={() => setClosed(true)}
        />
      )}
      <OnboardingStyles />
    </>
  );
}
