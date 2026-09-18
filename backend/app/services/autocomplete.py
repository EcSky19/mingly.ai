"""
Autocomplete providers for the professional profile onboarding fields.
See docs/professional-profile-design.md for the reasoning behind each
provider choice. Every function here fails open: on any error, returns
an empty list rather than raising, so the frontend field always falls
back to plain free text instead of breaking.
"""
import json
import logging
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.schemas.professional_profile import AutocompleteSuggestion

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_degrees_cache: list[str] | None = None
_fields_of_study_cache: list[str] | None = None
_industries_cache: list[str] | None = None
_languages_cache: list[str] | None = None


def _load_json_list(filename: str) -> list[str]:
    with open(DATA_DIR / filename) as f:
        return json.load(f)


async def autocomplete_companies(query: str) -> list[AutocompleteSuggestion]:
    """Live proxy to Clearbit's free Company Autocomplete API."""
    if not query or len(query) < 2:
        return []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                "https://autocomplete.clearbit.com/v1/companies/suggest",
                params={"query": query},
            )
            resp.raise_for_status()
            results = resp.json()
            return [
                AutocompleteSuggestion(value=r["name"], subtitle=r.get("domain"))
                for r in results
                if r.get("name")
            ][:10]
    except Exception as e:
        logger.warning(f"Company autocomplete failed, failing open: {e}")
        return []


async def autocomplete_schools(query: str) -> list[AutocompleteSuggestion]:
    """Live proxy to the free Hipolabs Universities API."""
    if not query or len(query) < 2:
        return []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                "http://universities.hipolabs.com/search",
                params={"name": query},
            )
            resp.raise_for_status()
            results = resp.json()
            return [
                AutocompleteSuggestion(value=r["name"], subtitle=r.get("country"))
                for r in results
                if r.get("name")
            ][:10]
    except Exception as e:
        logger.warning(f"School autocomplete failed, failing open: {e}")
        return []


PHOTON_BASE_URL = "https://photon.komoot.io/api/"
# Photon's usage policy welcomes end-user-triggered, moderate-volume use
# with a proper User-Agent identifying the app - see docs/location-design.md.
PHOTON_HEADERS = {"User-Agent": "Mingly.ai/1.0 (contact: hello@mingly.ai)"}


async def autocomplete_cities(query: str) -> list[AutocompleteSuggestion]:
    """Live proxy to Photon (komoot), an OSM-based geocoder explicitly
    designed for search-as-you-type. NOT Nominatim - Nominatim's usage
    policy explicitly forbids autocomplete use; Photon's own docs list
    "search-as-you-type" as a supported feature and its README points
    Nominatim users here for exactly this use case."""
    if not query or len(query) < 2:
        return []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                PHOTON_BASE_URL,
                params={"q": query, "layer": ["city", "locality"], "limit": 8},
                headers=PHOTON_HEADERS,
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                coords = feature.get("geometry", {}).get("coordinates", [None, None])
                name = props.get("name")
                if not name:
                    continue
                subtitle_parts = [p for p in [props.get("state"), props.get("country")] if p]
                results.append(
                    AutocompleteSuggestion(
                        value=name,
                        subtitle=", ".join(subtitle_parts) or None,
                        longitude=coords[0],
                        latitude=coords[1],
                    )
                )
            return results
    except Exception as e:
        logger.warning(f"City autocomplete failed, failing open: {e}")
        return []


async def autocomplete_neighborhoods(
    query: str, near_latitude: float | None = None, near_longitude: float | None = None
) -> list[AutocompleteSuggestion]:
    """Same provider as autocomplete_cities. Biased toward a specific
    city's coordinates when provided, so "Park Slope" search after
    selecting New York doesn't surface a same-named place elsewhere."""
    if not query or len(query) < 2:
        return []
    try:
        params: dict = {"q": query, "layer": ["district", "locality"], "limit": 8}
        if near_latitude is not None and near_longitude is not None:
            params["lat"] = near_latitude
            params["lon"] = near_longitude
            params["location_bias_scale"] = 0.5
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(PHOTON_BASE_URL, params=params, headers=PHOTON_HEADERS)
            resp.raise_for_status()
            data = resp.json()
            results = []
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                name = props.get("name")
                if not name:
                    continue
                subtitle_parts = [p for p in [props.get("city"), props.get("state")] if p]
                results.append(
                    AutocompleteSuggestion(value=name, subtitle=", ".join(subtitle_parts) or None)
                )
            return results
    except Exception as e:
        logger.warning(f"Neighborhood autocomplete failed, failing open: {e}")
        return []


def autocomplete_degrees(query: str) -> list[AutocompleteSuggestion]:
    """Static, bundled list - no network call. See app/data/degrees.json."""
    global _degrees_cache
    if _degrees_cache is None:
        _degrees_cache = _load_json_list("degrees.json")

    if not query:
        return [AutocompleteSuggestion(value=d) for d in _degrees_cache[:10]]

    q = query.lower()
    matches = [d for d in _degrees_cache if q in d.lower()]
    return [AutocompleteSuggestion(value=d) for d in matches[:10]]


def autocomplete_fields_of_study(query: str) -> list[AutocompleteSuggestion]:
    """Static, bundled starter list - see app/data/README.md for the
    honest scope note: this is not yet the full CIP taxonomy."""
    global _fields_of_study_cache
    if _fields_of_study_cache is None:
        _fields_of_study_cache = _load_json_list("fields_of_study_starter.json")

    if not query:
        return [AutocompleteSuggestion(value=f) for f in _fields_of_study_cache[:10]]

    q = query.lower()
    matches = [f for f in _fields_of_study_cache if q in f.lower()]
    return [AutocompleteSuggestion(value=f) for f in matches[:10]]


def autocomplete_industries(query: str) -> list[AutocompleteSuggestion]:
    """Static, bundled starter list - see app/data/README.md."""
    global _industries_cache
    if _industries_cache is None:
        _industries_cache = _load_json_list("industries_starter.json")

    if not query:
        return [AutocompleteSuggestion(value=i) for i in _industries_cache[:10]]

    q = query.lower()
    matches = [i for i in _industries_cache if q in i.lower()]
    return [AutocompleteSuggestion(value=i) for i in matches[:10]]


def autocomplete_languages(query: str) -> list[AutocompleteSuggestion]:
    """Static, bundled list - the complete official ISO 639-1 standard
    (184 languages), not a curated subset. See app/data/languages_starter.json."""
    global _languages_cache
    if _languages_cache is None:
        _languages_cache = _load_json_list("languages_starter.json")

    if not query:
        return [AutocompleteSuggestion(value=l) for l in _languages_cache[:10]]

    q = query.lower()
    matches = [l for l in _languages_cache if q in l.lower()]
    return [AutocompleteSuggestion(value=l) for l in matches[:10]]


def autocomplete_job_titles(db: Session, query: str) -> list[AutocompleteSuggestion]:
    """Queries the reference_job_titles table (seeded from O*NET - see
    app/data/README.md). Returns an empty list gracefully if the table
    hasn't been seeded yet, so the field falls back to free text."""
    if not query or len(query) < 2:
        return []
    try:
        from app.models.job_title import JobTitleReference

        stmt = (
            select(JobTitleReference.title)
            .where(JobTitleReference.title.ilike(f"%{query}%"))
            .distinct()
            .limit(10)
        )
        rows = db.execute(stmt).scalars().all()
        return [AutocompleteSuggestion(value=r) for r in rows]
    except Exception as e:
        logger.warning(f"Job title autocomplete failed, failing open: {e}")
        return []
