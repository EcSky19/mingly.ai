# Deploying to the Hetzner server

## One-time server setup

1. SSH into the server.
2. Install Docker + Compose plugin:
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```
3. Clone the repo:
   ```bash
   git clone https://github.com/EcSky19/mingly.ai.git
   cd mingly.ai
   ```
4. Create `.env` from `.env.example` and fill in real values:
   - `SESSION_SECRET`: generate with `openssl rand -hex 32`
   - `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET`: from the LinkedIn Developer app
   - `LINKEDIN_REDIRECT_URI`: `https://www.mingly.ai/api/auth/linkedin/callback`
   - `APP_URL`: `https://www.mingly.ai`
   - `NEXT_PUBLIC_API_URL`: `https://www.mingly.ai` (Caddy routes `/api/*` to the backend on the same domain)
   - `POSTGRES_PASSWORD`: generate a real one
5. DNS: point `www.mingly.ai` and `mingly.ai` A records at the server's IP.

## Every deploy after that

```bash
cd mingly.ai
git pull origin main
docker compose -f docker-compose.yml -f infrastructure/docker-compose.prod.yml up -d --build
docker compose exec backend alembic upgrade head
```

Caddy handles TLS certificate issuance/renewal automatically the first time it sees traffic for the domain - no manual certbot step needed.

## Rollback

```bash
git checkout <previous-commit-sha>
docker compose -f docker-compose.yml -f infrastructure/docker-compose.prod.yml up -d --build
```
