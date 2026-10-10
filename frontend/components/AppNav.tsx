import { useEffect, useState } from "react";
import { useRouter } from "next/router";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const LINKS = [
  { href: "/home", label: "Discover" },
  { href: "/matches", label: "Matches" },
  { href: "/messages", label: "Messages" },
  { href: "/circle", label: "My Circle" },
  { href: "/profile", label: "My Profile" },
  { href: "/settings", label: "Settings" },
];

// Shared top bar for the signed-in app pages, so navigation stays
// consistent instead of being re-implemented on each page.
export default function AppNav() {
  const router = useRouter();
  // The Admin link only appears for admin accounts. The admin area itself is
  // protected on the server - this just keeps the nav uncluttered for everyone else.
  const [isAdmin, setIsAdmin] = useState(false);
  useEffect(() => {
    fetch(`${API_URL}/api/auth/me`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setIsAdmin(Boolean(d?.is_admin)))
      .catch(() => {});
  }, []);

  // Unread badge on Messages: conversations with something new. Checked on
  // every page change and every 30 seconds while the tab is visible.
  const [unread, setUnread] = useState(0);
  useEffect(() => {
    let cancelled = false;
    const check = () =>
      fetch(`${API_URL}/api/messages/unread`, { credentials: "include" })
        .then((r) => (r.ok ? r.json() : null))
        .then((d) => !cancelled && d && setUnread(d.conversations))
        .catch(() => {});
    check();
    const timer = setInterval(() => document.visibilityState === "visible" && check(), 30000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [router.asPath]);

  // The onboarding pages are where you edit your profile, so My Profile
  // stays highlighted there too.
  function isActive(href: string) {
    if (href === "/profile") return router.pathname === "/profile" || router.pathname.startsWith("/onboarding");
    if (href === "/messages") return router.pathname.startsWith("/messages");
    return router.pathname === href;
  }

  async function handleLogout() {
    try {
      await fetch(`${API_URL}/api/auth/logout`, { method: "POST", credentials: "include" });
    } catch {
      // Fails open - worst case they see the sign-in page next visit anyway.
    }
    router.push("/");
  }

  return (
    <div className="discover-topbar">
      <span className="wordmark">
        <img src="/mingly-mark.png" alt="" className="mark" />
        <span>Mingly.ai</span>
      </span>
      <nav className="discover-nav">
        {LINKS.map((link) => (
          <button
            key={link.href}
            type="button"
            className={isActive(link.href) ? "discover-nav-link discover-nav-link-active" : "discover-nav-link"}
            onClick={() => router.push(link.href)}
          >
            {link.label}
            {link.href === "/messages" && unread > 0 && (
              <span className="nav-badge" aria-label={`${unread} unread`}>{unread}</span>
            )}
          </button>
        ))}
        {isAdmin && (
          <button
            type="button"
            className={isActive("/admin") ? "discover-nav-link discover-nav-link-active" : "discover-nav-link"}
            onClick={() => router.push("/admin")}
          >
            Admin
          </button>
        )}
        <button type="button" className="discover-nav-link" onClick={handleLogout}>
          Log out
        </button>
      </nav>
    </div>
  );
}
