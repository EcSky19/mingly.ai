import Head from "next/head";

export default function ComingSoon() {
  return (
    <>
      <Head>
        <title>Mingly.ai — Meet your kind of people</title>
        <meta
          name="description"
          content="A social community for career-oriented professionals to build a life outside of work. Launching in New York City."
        />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Public+Sans:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </Head>

      <main className="page">
        <div className="content">
          <div className="wordmark">
            <img src="/mingly-mark.png" alt="" className="mark" />
            <span>Mingly.ai</span>
          </div>

          <h1 className="headline">
            Meet your
            <br />
            kind of people.
          </h1>

          <p className="subhead">
            A social community for career-oriented professionals to build a
            life outside of work — real people, real activities, real
            friendships.
          </p>

          <div className="actions">
            <a className="cta" href="mailto:hello@mingly.ai?subject=Early access">
              Get early access
            </a>
            <span className="location">Launching in New York City</span>
          </div>
        </div>

        <div className="motif" aria-hidden="true">
          <svg viewBox="0 0 520 520" className="rings">
            <circle className="ring ring-a" cx="230" cy="230" r="150" />
            <circle className="ring ring-b" cx="330" cy="290" r="120" />
            <circle className="ring ring-c" cx="180" cy="330" r="90" />
          </svg>
        </div>
      </main>

      <style>{`
        * {
          box-sizing: border-box;
        }
        html,
        body {
          margin: 0;
          padding: 0;
          background: #1b1730;
        }

        .page {
          min-height: 100vh;
          display: grid;
          grid-template-columns: 1.1fr 0.9fr;
          align-items: center;
          background: radial-gradient(
              120% 140% at 100% 0%,
              #241f3d 0%,
              #1b1730 55%
            ),
            #1b1730;
          font-family: "Public Sans", sans-serif;
          color: #f6f1e7;
          overflow: hidden;
        }

        .content {
          padding: 8vh 7vw;
          max-width: 640px;
          animation: rise 900ms ease-out both;
        }

        .wordmark {
          display: flex;
          align-items: center;
          gap: 0.6rem;
          margin-bottom: 3.5rem;
        }

        .mark {
          height: 1.7rem;
          width: auto;
          display: block;
        }

        .wordmark span {
          font-family: "Fraunces", serif;
          font-size: 1.05rem;
          font-weight: 500;
          letter-spacing: 0.02em;
          color: #e8a548;
        }

        .headline {
          font-family: "Fraunces", serif;
          font-weight: 600;
          font-size: clamp(2.6rem, 6vw, 4.4rem);
          line-height: 1.04;
          letter-spacing: -0.01em;
          margin: 0 0 1.75rem 0;
          color: #f6f1e7;
        }

        .subhead {
          font-size: 1.1rem;
          line-height: 1.6;
          color: #b9afd1;
          max-width: 30em;
          margin: 0 0 2.75rem 0;
        }

        .actions {
          display: flex;
          align-items: center;
          gap: 1.5rem;
          flex-wrap: wrap;
        }

        .cta {
          display: inline-block;
          background: #e8a548;
          color: #1b1730;
          font-weight: 600;
          font-size: 1rem;
          padding: 0.85rem 1.75rem;
          border-radius: 4px;
          text-decoration: none;
          transition: transform 150ms ease, background 150ms ease;
        }

        .cta:hover {
          background: #f2b768;
          transform: translateY(-1px);
        }

        .location {
          font-size: 0.9rem;
          color: #8f84ad;
        }

        .motif {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
          animation: rise 1100ms ease-out both;
        }

        .rings {
          width: min(70%, 420px);
          height: auto;
        }

        .ring {
          fill: none;
          stroke-width: 1.5;
        }

        .ring-a {
          stroke: #e8a548;
          opacity: 0.9;
        }

        .ring-b {
          stroke: #7c6baf;
          opacity: 0.75;
        }

        .ring-c {
          stroke: #b9afd1;
          opacity: 0.5;
        }

        @keyframes rise {
          from {
            opacity: 0;
            transform: translateY(14px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .content,
          .motif {
            animation: none;
          }
        }

        @media (max-width: 860px) {
          .page {
            grid-template-columns: 1fr;
          }
          .motif {
            order: -1;
            height: 34vh;
            opacity: 0.6;
          }
          .content {
            padding: 4vh 7vw 8vh;
          }
        }
      `}</style>
    </>
  );
}
