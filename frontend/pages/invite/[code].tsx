import Head from "next/head";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import OnboardingStyles from "../../components/OnboardingStyles";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type InviteInfo = { inviter_first_name: string; inviter_photo_url?: string | null };

function resolveUrl(url: string): string {
  return /^https?:\/\//.test(url) ? url : `${API_URL}${url}`;
}

// Where an invite link lands: who invited you, and one button to sign in.
// The invite code rides along through LinkedIn sign-in, so afterwards you
// can add them to your circle in one tap.
export default function Invite() {
  const router = useRouter();
  const code = typeof router.query.code === "string" ? router.query.code : "";
  const [info, setInfo] = useState<InviteInfo | null>(null);
  const [invalid, setInvalid] = useState(false);

  useEffect(() => {
    if (!code) return;
    fetch(`${API_URL}/api/invites/${encodeURIComponent(code)}`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setInfo)
      .catch(() => setInvalid(true));
  }, [code]);

  const signInUrl = `${API_URL}/api/auth/linkedin/login${info ? `?invite=${encodeURIComponent(code)}` : ""}`;

  return (
    <>
      <Head>
        <title>{info ? `${info.inviter_first_name} invited you to Mingly.ai` : "You're invited to Mingly.ai"}</title>
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

          <div className="invite-card">
            {info?.inviter_photo_url && <img src={resolveUrl(info.inviter_photo_url)} alt="" className="invite-avatar" />}
            <h1 className="headline">
              {info ? `${info.inviter_first_name} invited you to Mingly.ai` : invalid ? "Join Mingly.ai" : "You're invited"}
            </h1>
            <p className="subhead">
              {invalid
                ? "This invite link isn't valid anymore, but you're still welcome to join."
                : "Meet people who are into the same things you are - and keep your friends close in your circle."}
            </p>
            <a className="cta" href={signInUrl} style={{ display: "inline-block", textDecoration: "none" }}>
              Continue with LinkedIn
            </a>
            {info && (
              <p className="section-hint" style={{ marginTop: "1rem" }}>
                After you sign in, you can add {info.inviter_first_name} to your circle in one tap.
              </p>
            )}
          </div>
        </div>
      </main>
      <OnboardingStyles />
    </>
  );
}
