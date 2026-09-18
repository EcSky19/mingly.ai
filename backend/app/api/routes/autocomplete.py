"""
Autocomplete endpoints for the professional profile onboarding fields.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.professional_profile import AutocompleteSuggestion
from app.services import autocomplete

router = APIRouter(prefix="/api", tags=["autocomplete"])


@router.get("/cities/autocomplete", response_model=list[AutocompleteSuggestion])
async def cities_autocomplete(q: str = Query(default="", max_length=100)):
    return await autocomplete.autocomplete_cities(q)


@router.get("/neighborhoods/autocomplete", response_model=list[AutocompleteSuggestion])
async def neighborhoods_autocomplete(
    q: str = Query(default="", max_length=100),
    near_lat: float | None = Query(default=None),
    near_lon: float | None = Query(default=None),
):
    return await autocomplete.autocomplete_neighborhoods(q, near_lat, near_lon)


@router.get("/companies/autocomplete", response_model=list[AutocompleteSuggestion])
async def companies_autocomplete(q: str = Query(default="", max_length=100)):
    return await autocomplete.autocomplete_companies(q)


@router.get("/schools/autocomplete", response_model=list[AutocompleteSuggestion])
async def schools_autocomplete(q: str = Query(default="", max_length=100)):
    return await autocomplete.autocomplete_schools(q)


@router.get("/degrees/autocomplete", response_model=list[AutocompleteSuggestion])
def degrees_autocomplete(q: str = Query(default="", max_length=100)):
    return autocomplete.autocomplete_degrees(q)


@router.get("/fields-of-study/autocomplete", response_model=list[AutocompleteSuggestion])
def fields_of_study_autocomplete(q: str = Query(default="", max_length=100)):
    return autocomplete.autocomplete_fields_of_study(q)


@router.get("/industries/autocomplete", response_model=list[AutocompleteSuggestion])
def industries_autocomplete(q: str = Query(default="", max_length=100)):
    return autocomplete.autocomplete_industries(q)


@router.get("/languages/autocomplete", response_model=list[AutocompleteSuggestion])
def languages_autocomplete(q: str = Query(default="", max_length=100)):
    return autocomplete.autocomplete_languages(q)


@router.get("/job-titles/autocomplete", response_model=list[AutocompleteSuggestion])
def job_titles_autocomplete(q: str = Query(default="", max_length=100), db: Session = Depends(get_db)):
    return autocomplete.autocomplete_job_titles(db, q)
