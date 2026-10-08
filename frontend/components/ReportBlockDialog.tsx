import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const REASONS: { value: string; label: string }[] = [
  { value: "harassment", label: "Harassment" },
  { value: "unwanted_romantic_behavior", label: "Unwanted romantic behavior" },
  { value: "safety_concern", label: "Safety concern" },
  { value: "inappropriate_behavior", label: "Inappropriate behavior" },
  { value: "fake_profile", label: "Fake profile" },
  { value: "misrepresented_profile", label: "Misrepresented profile" },
  { value: "recruiting_or_referrals", label: "Recruiting or asking for referrals" },
  { value: "sales_outreach", label: "Sales outreach" },
  { value: "spam", label: "Spam" },
  { value: "other", label: "Something else" },
];

type Props = {
  userId: string;
  firstName: string;
  onClose: () => void;
  // Called after a successful block (alone or with a report) so the page can
  // remove the person right away.
  onBlocked: () => void;
};

// One shared flow for Discover, Matches, and My Circle: report (which also
// blocks by default) or just block. The other person is never told.
export default function ReportBlockDialog({ userId, firstName, onClose, onBlocked }: Props) {
  const [mode, setMode] = useState<"choose" | "report">("choose");
  const [reason, setReason] = useState("");
  const [details, setDetails] = useState("");
  const [alsoBlock, setAlsoBlock] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState("");

  async function send(path: string, body: object, success: string, blocked: boolean) {
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error();
      setDone(success);
      if (blocked) onBlocked();
    } catch {
      setError("Couldn't send that - please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="dialog-backdrop" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        {done ? (
          <>
            <h2 className="match-name">Thanks for letting us know</h2>
            <p className="section-hint">{done}</p>
            <div className="dialog-actions">
              <button type="button" className="cta" onClick={onClose}>Done</button>
            </div>
          </>
        ) : mode === "choose" ? (
          <>
            <h2 className="match-name">{firstName}</h2>
            <p className="section-hint">
              Blocking removes you from each other's Discover, matches, and circles. {firstName} won't be told.
            </p>
            {error && <p className="section-hint" style={{ color: "#f472b6" }}>{error}</p>}
            <div className="dialog-actions dialog-actions-stacked">
              <button type="button" className="discover-pass-btn" disabled={busy}
                onClick={() => send("/api/blocks", { user_id: userId }, `You won't see ${firstName} again, and they won't see you.`, true)}>
                Block {firstName}
              </button>
              <button type="button" className="discover-pass-btn" disabled={busy} onClick={() => setMode("report")}>
                Report {firstName}
              </button>
              <button type="button" className="match-unmatch" onClick={onClose}>Cancel</button>
            </div>
          </>
        ) : (
          <>
            <h2 className="match-name">Report {firstName}</h2>
            <p className="section-hint">
              Mingly is for building your life outside of work - not dating pressure, recruiting, or sales. Reports go to
              the Mingly team and are kept private.
            </p>
            <div className="field">
              <label className="field-label">What happened?</label>
              <select className="field-input" value={reason} onChange={(e) => setReason(e.target.value)}>
                <option value="">Choose a reason</option>
                {REASONS.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
            </div>
            <div className="field">
              <label className="field-label">Anything else we should know? (optional)</label>
              <textarea className="field-input" rows={3} maxLength={2000} value={details} onChange={(e) => setDetails(e.target.value)} />
            </div>
            <label className="dialog-check">
              <input type="checkbox" checked={alsoBlock} onChange={(e) => setAlsoBlock(e.target.checked)} />
              Also block {firstName}
            </label>
            {error && <p className="section-hint" style={{ color: "#f472b6" }}>{error}</p>}
            <div className="dialog-actions">
              <button type="button" className="match-unmatch" onClick={() => setMode("choose")}>Back</button>
              <button type="button" className="cta" disabled={busy || !reason}
                onClick={() => send("/api/reports", { user_id: userId, reason, details: details.trim() || null, also_block: alsoBlock },
                  alsoBlock ? `We'll review your report. You won't see ${firstName} again.` : "We'll review your report.", alsoBlock)}>
                {busy ? "Sending…" : "Send report"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
