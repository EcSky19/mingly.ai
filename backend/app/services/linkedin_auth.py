"""
LinkedIn OpenID Connect flow ("Sign In with LinkedIn using OpenID Connect").

We use OIDC (not the older r_liteprofile/r_emailaddress scopes) because it's
the currently supported, simplest path to just identity + email - which is
all we need. We are NOT scraping LinkedIn or pulling full profile data;
professional details are entered by the user during onboarding (see PRD).
"""
import secrets
from urllib.parse import urlencode

import httpx

from app.core.config import settings

AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

SCOPES = "openid profile email"


def build_authorization_url() -> tuple[str, str]:
    """Returns (redirect_url, state). Caller must persist `state` in the session
    and verify it on callback to prevent CSRF."""
    state = secrets.token_urlsafe(24)
    params = {
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "state": state,
        "scope": SCOPES,
    }
    return f"{AUTHORIZATION_URL}?{urlencode(params)}", state


async def exchange_code_for_token(code: str) -> str:
    """Exchanges the authorization code for an access token. Raises on failure."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
                "client_id": settings.LINKEDIN_CLIENT_ID,
                "client_secret": settings.LINKEDIN_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def fetch_userinfo(access_token: str) -> dict:
    """Fetches the OIDC userinfo claims: sub, email, given_name, family_name, picture."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()
