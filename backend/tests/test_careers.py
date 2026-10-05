"""Unit tests for career similarity (app/services/careers.py)."""
import json
from pathlib import Path

import pytest

from app.services.careers import career_family, core_role, core_role_display, family_phrase

CATALOG = Path(__file__).resolve().parent.parent / "app" / "data" / "job_titles_starter.json"
GENERIC_TITLES = {"Analyst", "Associate", "Senior Associate", "Vice President", "Director"}


def _catalog_titles():
    return [t if isinstance(t, str) else t.get("title", t.get("name")) for t in json.loads(CATALOG.read_text())]


def test_every_catalog_title_has_a_family_except_the_generic_ones():
    """Guard: adding a title to the autocomplete catalog without giving it a
    family would silently drop it out of career matching."""
    unmapped = {t for t in _catalog_titles() if career_family(t) is None}
    assert unmapped == GENERIC_TITLES, f"titles missing a career family: {unmapped - GENERIC_TITLES}"


@pytest.mark.parametrize("a,b", [
    ("Senior Product Manager", "Product Manager"),
    ("Staff Software Engineer", "Software Engineer"),
    ("Lead Data Scientist", "data scientist"),
    ("Senior Associate", "Associate"),
])
def test_seniority_does_not_change_the_core_role(a, b):
    assert core_role(a) == core_role(b)


def test_core_role_display_keeps_capitalization():
    assert core_role_display("Senior Data Scientist") == "Data Scientist"
    assert core_role_display("Lead UX Designer") == "UX Designer"


@pytest.mark.parametrize("title,family", [
    ("Data Scientist", "data"),
    ("Data Engineer", "data"),
    ("Senior iOS Developer", "software"),
    ("Software Architect", "software"),
    ("Landscape Architect", "engineering"),
    ("Head of Growth", "marketing"),
    ("Clinical Psychologist", "counseling"),
    ("Sous Chef", "hospitality"),
    ("Associate Attorney", "legal"),
])
def test_custom_titles_fall_into_sensible_families(title, family):
    assert career_family(title) == family


@pytest.mark.parametrize("title", ["Barista", "", None, "Analyst", "Director"])
def test_no_family_rather_than_a_false_match(title):
    assert career_family(title) is None


def test_family_phrases_read_naturally():
    assert family_phrase("data") == "data and analytics"
    assert family_phrase("software") == "software engineering"
