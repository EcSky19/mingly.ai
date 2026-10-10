from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.api.routes import auth, autocomplete, professional_profile, education, locations, interests, activities, languages, social_profile, pets, photos, interactions, discover, match_contact, matches, circle, safety, admin, messages

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
app.include_router(education.router)
app.include_router(locations.router)
app.include_router(interests.router)
app.include_router(interests.catalog_router)
app.include_router(activities.router)
app.include_router(activities.catalog_router)
app.include_router(languages.router)
app.include_router(social_profile.router)
app.include_router(pets.router)
app.include_router(photos.router)
app.include_router(interactions.router)
app.include_router(discover.router)
app.include_router(match_contact.router)
app.include_router(matches.router)
app.include_router(circle.router)
app.include_router(circle.invites_router)
app.include_router(safety.router)
app.include_router(admin.router)
app.include_router(messages.router)

# Serve uploaded profile photos as static files. The uploads directory
# is created here if missing (StaticFiles requires it to exist at
# mount time) and lives at backend/uploads, which the existing
# ./backend:/app Docker bind mount already persists to host disk - see
# app/services/photo_storage.py for the full storage design.
_uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
_uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=str(_uploads_dir)), name="uploads")


@app.get("/api/health")
async def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
