import Head from "next/head";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import OnboardingStyles from "../components/OnboardingStyles";
import AppNav from "../components/AppNav";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Person = { id: string; first_name: string; last_name: string; email: string; account_status: string };
type Report = {
  id: string;
  reason: string;
  details?: string | null;
  status: string;
  admin_note?: string | null;
  created_at?: string | null;
  reporter?: Person | null;
  reported: Person;
  reports_against_reported: number;
};
type Tab = "open" | "actioned" | "dismissed";

const REASON_LABELS: Record<string, string> = {
  harassment: "Harassment",
  unwanted_romantic_behavior: "Unwanted romantic behavior",
  safety_concern: "Safety concern",
  inappropriate_behavior: "Inappropriate behavior",
  fake_profile: "Fake profile",
  misrepresented_profile: "Misrepresented profile",
  recruiting_or_referrals: "Recruiting / referrals",
  sales_outreach: "Sales outreach",
  spam: "Spam",
  other: "Other",
};

// Admin-only moderation queue. The server decides who's an admin; anyone
// else gets "not found" here, exactly like a missing page.
export default function Admin() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("open");
  const [reports, setReports] = useState<Report[] | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  function load(which: Tab) {
    setReports(null);
    fetch(`${API_URL}/api/admin/reports?status=${which}`, { credentials: "include" })
      .then((r) => {
        if (r.status === 401) router.replace("/");
        if (r.status === 404) setNotFound(true);
        return r.ok ? r.json() : Promise.reject();
      })
      .then(setReports)
      .catch(() => setReports([]));
  }

  useEffect(() => load(tab), [tab]);

  async function act(report: Report, kind: "dismiss" | "active" | "suspended" | "banned") {
    const label = kind === "dismiss" ? "dismiss this report" : kind === "active" ? `reactivate ${report.reported.first_name}` : `${kind === "banned" ? "ban" : "suspend"} ${report.reported.first_name}`;
    if (!window.confirm(`Are you sure you want to ${label}?`)) return;
    setBusy(report.id);
    setError("");
    const note = (notes[report.id] || "").trim() || null;
    const res = await fetch(
      kind === "dismiss" ? `${API_URL}/api/admin/reports/${report.id}/dismiss` : `${API_URL}/api/admin/users/${report.reported.id}/status`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(kind === "dismiss" ? { note } : { status: kind, note, report_id: report.status === "open" ? report.id : null }),
      },
    ).catch(() => null);
    setBusy("");
    if (!res || !res.ok) {
      setError("That didn't go through - please try again.");
      return;
    }
    load(tab);
  }

  return (
    <>
      <Head>
        <title>Admin — Mingly.ai</title>
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
          {notFound ? (
            <>
              <h1 className="headline">Page not found</h1>
              <button type="button" className="cta" onClick={() => router.push("/home")}>Go to Discover</button>
            </>
          ) : (
            <>
              <h1 className="headline">Reports</h1>
              <p className="subhead">Every action here is recorded with your name. Reporters are never revealed to the people they report.</p>
              <div className="admin-tabs">
                {(["open", "actioned", "dismissed"] as Tab[]).map((t) => (
                  <button key={t} type="button" className={t === tab ? "discover-nav-link discover-nav-link-active" : "discover-nav-link"} onClick={() => setTab(t)}>
                    {t === "open" ? "Open" : t === "actioned" ? "Actioned" : "Dismissed"}
                  </button>
                ))}
              </div>
              {error && <p className="section-hint" style={{ color: "#f472b6" }}>{error}</p>}
              {reports === null && <p className="section-hint">Loading…</p>}
              {reports && reports.length === 0 && <p className="section-hint">Nothing here.</p>}
              <div className="matches-grid">
                {(reports || []).map((r) => (
                  <div className="match-card" key={r.id}>
                    <p className="discover-label" style={{ marginTop: 0 }}>
                      {REASON_LABELS[r.reason] || r.reason}
                      {r.created_at ? ` · ${new Date(r.created_at).toLocaleDateString()}` : ""}
                    </p>
                    <h2 className="match-name">
                      {r.reported.first_name} {r.reported.last_name}
                    </h2>
                    <p className="match-meta">
                      {r.reported.email} · account {r.reported.account_status} · {r.reports_against_reported} report
                      {r.reports_against_reported === 1 ? "" : "s"} total
                    </p>
                    {r.details && <p className="admin-details">"{r.details}"</p>}
                    <p className="match-meta">
                      Reported by {r.reporter ? `${r.reporter.first_name} ${r.reporter.last_name} (${r.reporter.email})` : "a deleted account"}
                    </p>
                    {r.admin_note && <p className="match-meta">Note: {r.admin_note}</p>}
                    <div className="field" style={{ marginTop: "0.75rem" }}>
                      <input
                        className="field-input"
                        placeholder="Note for the audit log (optional)"
                        maxLength={2000}
                        value={notes[r.id] || ""}
                        onChange={(e) => setNotes((n) => ({ ...n, [r.id]: e.target.value }))}
                      />
                    </div>
                    <div className="circle-person-actions" style={{ flexWrap: "wrap" }}>
                      {r.status === "open" && (
                        <button type="button" className="discover-pass-btn" disabled={busy === r.id} onClick={() => act(r, "dismiss")}>Dismiss</button>
                      )}
                      {r.reported.account_status === "active" ? (
                        <>
                          <button type="button" className="discover-pass-btn" disabled={busy === r.id} onClick={() => act(r, "suspended")}>Suspend</button>
                          <button type="button" className="settings-delete-btn" disabled={busy === r.id} onClick={() => act(r, "banned")}>Ban</button>
                        </>
                      ) : (
                        <button type="button" className="discover-pass-btn" disabled={busy === r.id} onClick={() => act(r, "active")}>Reactivate</button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </main>
      <OnboardingStyles />
    </>
  );
}
