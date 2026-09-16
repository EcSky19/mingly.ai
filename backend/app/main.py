from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.api.routes import auth, autocomplete, professional_profile

app = FastAPI(title="Mingly.ai API", version="0.1.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    session_cookie=settings.SESSION_COOKIE_NAME,
    max_age=settings.SESSION_MAX_AGE_SECONDS,
    same_site="lax",
    https_only=settings.ENVIRONMENT == "production",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.APP_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(autocomplete.router)
app.include_router(professional_profile.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
