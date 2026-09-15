const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  return (
    <main style={{
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      fontFamily: "system-ui, sans-serif",
      textAlign: "center",
      padding: "2rem",
    }}>
      <h1 style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>Mingly.ai</h1>
      <p style={{ color: "#555", marginBottom: "2rem", maxWidth: 420 }}>
        Meet your kind of people. A community for career-oriented professionals
        to build their life outside of work.
      </p>
      <a
        href={`${API_URL}/api/auth/linkedin/login`}
        style={{
          background: "#0A66C2",
          color: "white",
          padding: "0.75rem 1.5rem",
          borderRadius: 8,
          textDecoration: "none",
          fontWeight: 600,
        }}
      >
        Continue with LinkedIn
      </a>
    </main>
  );
}
