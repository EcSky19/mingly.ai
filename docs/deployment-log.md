# Deployment Log

## 2026-09-16 — Backend, database, and LinkedIn auth deployed. Week 1 complete.

**Backend + database:** deployed via `docker compose up -d --build db backend`. Backend on host port 8010 (8000 was taken by CareerRadar), Postgres+pgvector not exposed to the host at all — only reachable internally via the Docker network. Migration `0001_initial_users` applied successfully (fixed a bug first: the enum type was being created twice — caught and fixed by testing against a real local Postgres+pgvector instance before redeploying).

**nginx:** added `/api/` routing to the existing `mingly-ai` site config (proxies to backend on 8010), inserted via script to avoid manual edit errors, verified with `nginx -t` before reload.

**LinkedIn OAuth:** tested end to end with a real LinkedIn account. Login → LinkedIn consent → callback → user record created in production database → redirect to onboarding, all confirmed working.

**Week 1 exit test: passed.** `www.mingly.ai` is live, LinkedIn login works, a real user record exists in the production database.

## 2026-09-16 — First deploy: Coming Soon page

**Server:** shared Hetzner box (also runs CareerRadar, sma-engine, taengine — see notes below), 2 vCPU / 4GB RAM / 40GB disk, Helsinki.

**What's deployed:** the Next.js frontend (`frontend/`) only, serving the Coming Soon landing page. Backend, Postgres, and pgvector are not deployed yet — not needed until LinkedIn auth and onboarding are ready to go live.

**Port allocation on this server** (shared with other projects — do not reuse):
| Port | Used by |
|---|---|
| 8000 | CareerRadar backend (existing) |
| 3000 | An existing Next.js app (existing) |
| 3001 | sma-engine (existing) |
| **3010** | **Mingly.ai frontend (new)** |

**nginx:** existing sites (`career-radar`, `career-radar-frontend`, `default`, `sma-engine`, `taengine.mingly.ai`) were not modified. Added a new site config `mingly-ai` (see `infrastructure/nginx/mingly-ai.conf`) that proxies `mingly.ai` / `www.mingly.ai` → `127.0.0.1:3010`.

**DNS (GoDaddy):** root `@` record was previously attached to GoDaddy's Website Builder product (serving a parked page) and had no dedicated `www` record — only a `www` CNAME pointing at the root. Fixed by disconnecting Website Builder and adding a plain A record for `@` → `204.168.186.74` (the existing `www` CNAME then resolves through automatically). Other subdomains (`api`, `careerradar`, `smaengine`, `taengine`) were already correctly configured and were not touched.

**TLS:** issued successfully via `certbot --nginx -d mingly.ai -d www.mingly.ai` on 2026-09-16, after DNS finished propagating. Certificate expires 2026-12-14, auto-renewal configured by Certbot.

**Status:** **live** — `https://www.mingly.ai` confirmed publicly reachable, serving the real Coming Soon page over HTTPS. Verified by fetching the URL directly.

**Not yet deployed:** backend API, Postgres+pgvector, LinkedIn auth (LinkedIn Developer app also still in setup — Company Page and app product pending).
