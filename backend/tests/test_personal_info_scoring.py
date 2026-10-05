"""
Tests for onboarding personal info in matching (languages, education,
professional, dogs, social goals, extended lifestyle). Two consent rules
apply to every signal:
  - it only COUNTS when both people allowed that field for matching;
  - it's only MENTIONED when the candidate made it visible on their profile.
"""
import uuid

import pytest
from sqlalchemy import event

from app.db.session import Base, engine, SessionLocal
from app.models.professional_profile import ProfessionalProfile
from app.models.user import User
from app.models.user_education import UserEducation
from app.models.user_language import UserLanguage
from app.models.user_location import UserLocation
from app.models.user_pet import UserPet
from app.models.user_social_profile import UserSocialProfile
from app.services.compatibility_scoring import get_ranked_candidates


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _person(db, name="Test"):
    u = User(linkedin_sub=f"t-{uuid.uuid4()}", email=f"t-{uuid.uuid4()}@example.com", first_name=name, last_name="U",
             account_status="active", onboarding_completed=True)
    db.add(u)
    db.flush()
    db.add(UserLocation(user_id=u.id, city="NYC", latitude=40.7128, longitude=-74.0060, travel_radius_miles=25, is_primary=True))
    db.commit()
    return u.id


def _rank(db, requester_id):
    return {sc.user.id: sc for sc in get_ranked_candidates(db, requester_id)}


def _lang(db, uid, language, visible=True, usable=True):
    db.add(UserLanguage(user_id=uid, language=language, visible_on_profile=visible, usable_for_matching=usable))
    db.commit()


def test_shared_language_counts_and_is_named_when_visible():
    db = SessionLocal()
    me, match, baseline = _person(db), _person(db, "Match"), _person(db, "Baseline")
    _lang(db, me, "Spanish")
    _lang(db, match, "Spanish")
    ranked = _rank(db, me)
    assert ranked[match].score > ranked[baseline].score
    assert "speak Spanish" in ranked[match].intro
    db.close()


def test_english_never_counts():
    db = SessionLocal()
    me, match, baseline = _person(db), _person(db, "Match"), _person(db, "Baseline")
    _lang(db, me, "English")
    _lang(db, match, "English")
    ranked = _rank(db, me)
    assert ranked[match].score == ranked[baseline].score
    assert "English" not in ranked[match].intro
    db.close()


def test_opted_out_language_counts_for_nothing():
    db = SessionLocal()
    me, match, baseline = _person(db), _person(db, "Match"), _person(db, "Baseline")
    _lang(db, me, "Spanish")
    _lang(db, match, "Spanish", usable=False)
    ranked = _rank(db, me)
    assert ranked[match].score == ranked[baseline].score
    assert "Spanish" not in ranked[match].intro
    db.close()


def test_hidden_school_counts_but_is_never_named():
    db = SessionLocal()
    me, match, baseline = _person(db), _person(db, "Match"), _person(db, "Baseline")
    db.add(UserEducation(user_id=me, school="Cornell", visible_on_profile=True, usable_for_matching=True))
    db.add(UserEducation(user_id=match, school="cornell ", visible_on_profile=False, usable_for_matching=True))
    db.commit()
    ranked = _rank(db, me)
    assert ranked[match].score > ranked[baseline].score, "case/whitespace-insensitive school match should count"
    assert "ornell" not in ranked[match].intro and not any("ornell" in r for r in ranked[match].reasons)
    db.close()


def test_industry_needs_both_opted_in_and_is_named_only_if_visible():
    db = SessionLocal()
    me, visible, hidden, opted_out = _person(db), _person(db, "V"), _person(db, "H"), _person(db, "O")
    for uid, vis, usable in ((me, True, True), (visible, True, True), (hidden, False, True), (opted_out, True, False)):
        db.add(ProfessionalProfile(user_id=uid, industry="Technology", industry_visible_on_profile=vis,
                                   industry_usable_for_matching=usable))
    db.commit()
    ranked = _rank(db, me)
    assert "work in technology" in ranked[visible].intro
    assert ranked[hidden].score == ranked[visible].score and "technology" not in ranked[hidden].intro
    assert ranked[opted_out].score < ranked[visible].score
    db.close()


def test_dog_compatibility_ordering():
    """Both dog people > one dog + other comfortable > no dog info > one
    dog + other explicitly not comfortable."""
    db = SessionLocal()
    me = _person(db)
    both, friendly, neutral, mismatch = (_person(db, n) for n in ("Both", "Friendly", "Neutral", "Mismatch"))
    db.add(UserPet(user_id=me, pet_type="dog", visible_on_profile=True, usable_for_matching=True))
    db.add(UserPet(user_id=both, pet_type="dog", visible_on_profile=True, usable_for_matching=True))
    db.add(UserSocialProfile(user_id=friendly, visible_on_profile=False, usable_for_matching=True, comfortable_with_dogs=True))
    db.add(UserSocialProfile(user_id=mismatch, visible_on_profile=False, usable_for_matching=True, comfortable_with_dogs=False))
    db.commit()
    s = {k: v.score for k, v in _rank(db, me).items()}
    assert s[both] > s[friendly] > s[neutral] > s[mismatch]
    assert "dog people" in _rank(db, me)[both].intro
    db.close()


def test_shared_goals_count_but_are_named_only_if_visible():
    db = SessionLocal()
    me, shown, hidden, baseline = _person(db), _person(db, "S"), _person(db, "H"), _person(db, "B")
    for uid, vis in ((me, True), (shown, True), (hidden, False)):
        db.add(UserSocialProfile(user_id=uid, visible_on_profile=vis, usable_for_matching=True, social_goals=["activity_partners"]))
    db.commit()
    ranked = _rank(db, me)
    assert ranked[shown].score > ranked[baseline].score
    assert ranked[hidden].score == ranked[shown].score
    assert "activity partners" in ranked[shown].intro
    assert "activity partners" not in ranked[hidden].intro
    db.close()


def test_non_answers_never_count_as_lifestyle_similarity():
    db = SessionLocal()
    me, match, baseline = _person(db), _person(db, "Match"), _person(db, "Baseline")
    either = dict(indoor_outdoor_preference="either", weekday_weekend_preference="either", early_bird_night_owl="either")
    db.add(UserSocialProfile(user_id=me, visible_on_profile=True, usable_for_matching=True, **either))
    db.add(UserSocialProfile(user_id=match, visible_on_profile=True, usable_for_matching=True, **either))
    db.commit()
    ranked = _rank(db, me)
    assert ranked[match].score == ranked[baseline].score
    db.close()


def test_similar_pace_scores_but_is_only_mentioned_if_visible():
    """Saying 'you move at a similar pace' reveals their lifestyle
    answers, which are hidden by default - so it's only said when they
    made their lifestyle section visible."""
    db = SessionLocal()
    me, shown, hidden = _person(db), _person(db, "S"), _person(db, "H")
    same = dict(activity_level="active", going_out_frequency="often", social_cadence="about_once_per_week")
    for uid, vis in ((me, True), (shown, True), (hidden, False)):
        db.add(UserSocialProfile(user_id=uid, visible_on_profile=vis, usable_for_matching=True, **same))
    db.commit()
    ranked = _rank(db, me)
    assert ranked[hidden].score == ranked[shown].score
    assert "pace" in ranked[shown].intro
    assert "pace" not in ranked[hidden].intro
    db.close()


def test_ranking_query_count_is_flat():
    """The personal-info lookups must be batched: ranking 2 candidates and
    8 candidates should execute the same number of SQL statements."""
    def scenario(n):
        db = SessionLocal()
        me = _person(db)
        _lang(db, me, "Spanish")
        for _ in range(n):
            uid = _person(db)
            _lang(db, uid, "Spanish")
            db.add(UserPet(user_id=uid, pet_type="dog", visible_on_profile=True, usable_for_matching=True))
            db.add(UserEducation(user_id=uid, school="Cornell", visible_on_profile=True, usable_for_matching=True))
            db.commit()
        db.close()
        return me

    def count(me):
        db = SessionLocal()
        n = 0

        def on_execute(*args, **kwargs):
            nonlocal n
            n += 1

        event.listen(db.bind, "before_cursor_execute", on_execute)
        try:
            get_ranked_candidates(db, me)
        finally:
            event.remove(db.bind, "before_cursor_execute", on_execute)
            db.close()
        return n

    # Isolate each scenario so earlier tests' users don't change the pool size
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    small = count(scenario(2))
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    large = count(scenario(8))
    assert small == large, f"2 candidates: {small} queries, 8 candidates: {large} - N+1 crept in"


# --- Career similarity, alumni, degree, proficiency, pets ---

def _role(db, uid, title, visible=True, usable=True):
    db.add(ProfessionalProfile(user_id=uid, current_role=title, current_role_visible_on_profile=visible,
                               current_role_usable_for_matching=usable))
    db.commit()


def _pet(db, uid, **kw):
    db.add(UserPet(user_id=uid, visible_on_profile=kw.pop("visible", True), usable_for_matching=kw.pop("usable", True), **kw))
    db.commit()


def test_career_similarity_tiers_and_consent():
    db = SessionLocal()
    me = _person(db)
    same, family, unrelated, hidden, opted_out, base = (_person(db, n) for n in ("Sam", "Dana", "Alex", "Hana", "Omar", "Base"))
    _role(db, me, "Data Scientist")
    _role(db, same, "Senior Data Scientist")
    _role(db, family, "Data Engineer")
    _role(db, unrelated, "Account Executive")
    _role(db, hidden, "Data Analyst", visible=False)
    _role(db, opted_out, "Data Analyst", usable=False)
    r = _rank(db, me)
    b = r[base].score
    assert r[same].score - b == 3 and "work as a data scientist" in r[same].intro, "shared CORE role, true for both"
    assert "senior" not in r[same].intro.lower(), "must not attribute their seniority to the requester"
    assert r[family].score - b == 2 and "work in data and analytics" in r[family].intro
    assert r[unrelated].score == b
    assert r[hidden].score - b == 2 and "data" not in r[hidden].intro.lower()
    assert r[opted_out].score == b
    db.close()


def test_alumni_count_strongly_regardless_of_graduation_year():
    db = SessionLocal()
    me, classmate, decades_apart, base = _person(db), _person(db, "C"), _person(db, "D"), _person(db, "B")
    db.add(UserEducation(user_id=me, school="Cornell", graduation_year=2015, visible_on_profile=True, usable_for_matching=True))
    db.add(UserEducation(user_id=classmate, school="Cornell", graduation_year=2015, visible_on_profile=True, usable_for_matching=True))
    db.add(UserEducation(user_id=decades_apart, school="Cornell", graduation_year=1990, visible_on_profile=True, usable_for_matching=True))
    db.commit()
    r = _rank(db, me)
    assert r[classmate].score - r[base].score == 8
    assert r[decades_apart].score == r[classmate].score, "graduation year must not change the alumni signal"
    db.close()


def test_same_degree_counts():
    db = SessionLocal()
    me, match, base = _person(db), _person(db, "M"), _person(db, "B")
    for uid in (me, match):
        db.add(UserEducation(user_id=uid, degree="Bachelor of Science (BS)", visible_on_profile=True, usable_for_matching=True))
    db.commit()
    r = _rank(db, me)
    assert r[match].score - r[base].score == 1
    db.close()


def test_a_language_learner_is_half_the_signal():
    db = SessionLocal()
    me, fluent, learner, base = _person(db), _person(db, "F"), _person(db, "L"), _person(db, "B")
    db.add(UserLanguage(user_id=me, language="Spanish", proficiency="fluent", visible_on_profile=True, usable_for_matching=True))
    db.add(UserLanguage(user_id=fluent, language="Spanish", proficiency="native", visible_on_profile=True, usable_for_matching=True))
    db.add(UserLanguage(user_id=learner, language="Spanish", proficiency="learning", visible_on_profile=True, usable_for_matching=True))
    db.commit()
    r = _rank(db, me)
    assert r[fluent].score - r[base].score == 3
    assert r[learner].score - r[base].score == 1.5
    db.close()


def test_cats_and_other_pets_count():
    db = SessionLocal()
    me = _person(db)
    cat, other, base = _person(db, "Cat"), _person(db, "Other"), _person(db, "Base")
    _pet(db, me, pet_type="cat")
    _pet(db, cat, pet_type="cat")
    _pet(db, other, pet_type="other")
    r = _rank(db, me)
    assert r[cat].score - r[base].score == 2 and "cat people" in r[cat].intro
    assert r[other].score - r[base].score == 1, "both have pets, different kinds"
    db.close()


def test_hidden_cat_counts_but_is_not_named():
    db = SessionLocal()
    me, cat = _person(db), _person(db, "Cat")
    _pet(db, me, pet_type="cat")
    _pet(db, cat, pet_type="cat", visible=False)
    assert "cat" not in _rank(db, me)[cat].intro
    db.close()


def test_dog_details_matter():
    db = SessionLocal()
    me = _person(db)
    matched, mismatched, unsocial = _person(db, "M"), _person(db, "X"), _person(db, "U")
    _pet(db, me, pet_type="dog", size="large", activity_level="high", comfortable_with_other_dogs=True)
    _pet(db, matched, pet_type="dog", size="large", activity_level="high", comfortable_with_other_dogs=True)
    _pet(db, mismatched, pet_type="dog", size="small", activity_level="low", comfortable_with_other_dogs=True)
    _pet(db, unsocial, pet_type="dog", size="small", activity_level="low", comfortable_with_other_dogs=False)
    s = {k: v.score for k, v in _rank(db, me).items()}
    assert s[matched] - s[mismatched] == 2, "same size +1 and same energy +1"
    assert s[mismatched] - s[unsocial] == 2, "a dog not comfortable around other dogs drops the bonus from 3 to 1"
    db.close()
