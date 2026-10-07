import { useRouter } from "next/router";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const LINKS = [
  { href: "/home", label: "Discover" },
  { href: "/matches", label: "Matches" },
  { href: "/circle", label: "My Circle" },
  { href: "/profile", label: "My Profile" },
];

// Shared top bar for the signed-in app pages, so navigation stays
// consistent instead of being re-implemented on each page.
export default function AppNav() {
  const router = useRouter();

  // The onboarding pages are where you edit your profile, so My Profile
  // stays highlighted there too.
  function isActive(href: string) {
    if (href === "/profile") return router.pathname === "/profile" || router.pathname.startsWith("/onboarding");
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
          </button>
        ))}
        <button type="button" className="discover-nav-link" onClick={handleLogout}>
          Log out
        </button>
      </nav>
    </div>
  );
}
