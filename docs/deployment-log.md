# Deployment Log

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

**TLS:** not yet issued — first Certbot attempt failed because DNS hadn't propagated yet (old GoDaddy parking IPs were still being served). Waiting on propagation, will retry `certbot --nginx -d mingly.ai -d www.mingly.ai`.

**Status:** container running and verified serving real content locally on the server (`curl localhost:3010` returns the actual page). Public HTTPS access pending DNS propagation + Certbot.

**Not yet deployed:** backend API, Postgres+pgvector, LinkedIn auth (LinkedIn Developer app also still in setup — Company Page and app product pending).
