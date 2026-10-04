"""
Career similarity for matching: connects people with similar careers, not
just identical job titles.

Two tiers:
  - same core role: titles that differ only by seniority ("Senior Product
    Manager" vs "Product Manager") are the same role;
  - same career family: related roles in the same field ("Data Scientist"
    and "Data Analyst", "Product Manager" and "Scrum Master" are not the
    same family, but "Data Scientist" and "Data Engineer" are).

Every title in the autocomplete catalog (app/data/job_titles_starter.json)
is mapped explicitly; custom titles typed outside the list fall back to
keyword rules. Generic titles that could mean anything ("Analyst",
"Associate", "Director", "Vice President") deliberately get no family -
they only ever count on an exact core-role match.
"""

# family key -> (natural phrase for "you both work in ...", catalog titles)
CAREER_FAMILIES: dict[str, tuple[str, list[str]]] = {
    "software": ("software engineering", [
        "Software Engineer", "Senior Software Engineer", "Staff Software Engineer", "Frontend Engineer",
        "Backend Engineer", "Full Stack Engineer", "DevOps Engineer", "Site Reliability Engineer",
        "Security Engineer", "QA Engineer", "Solutions Architect", "Engineering Manager",
        "Director of Engineering", "VP of Engineering", "CTO",
    ]),
    "data": ("data and analytics", [
        "Data Scientist", "Data Analyst", "Data Engineer", "Machine Learning Engineer",
    ]),
    "product": ("product management", ["Product Manager", "Senior Product Manager"]),
    "design": ("design", [
        "Product Designer", "UX Designer", "UI Designer", "Graphic Designer", "Art Director",
        "Photographer", "Videographer",
    ]),
    "founders": ("building companies", ["CEO", "COO", "Founder", "Co-Founder", "Founder & CEO"]),
    "marketing": ("marketing", [
        "Marketing Manager", "Growth Marketing Manager", "Content Marketing Manager", "Social Media Manager",
        "Brand Manager", "Marketing Director", "CMO", "Growth Hacker", "Community Manager",
    ]),
    "sales": ("sales and business development", [
        "Sales Representative", "Account Executive", "Sales Manager", "Sales Director",
        "Business Development Manager", "Customer Success Manager",
    ]),
    "operations": ("operations", [
        "Operations Manager", "Business Operations Analyst", "Chief of Staff", "Office Manager",
        "Administrative Assistant", "Executive Assistant",
    ]),
    "finance": ("finance", [
        "Financial Analyst", "Investment Banking Analyst", "Portfolio Manager", "Accountant", "Controller",
        "CPA", "CFO",
    ]),
    "consulting": ("consulting", ["Consultant", "Management Consultant", "Strategy Consultant"]),
    "people": ("HR and recruiting", ["HR Manager", "Recruiter", "Talent Acquisition Manager", "People Operations Manager"]),
    "healthcare": ("healthcare", [
        "Registered Nurse", "Physician", "Nurse Practitioner", "Physician Assistant", "Pharmacist",
        "Physical Therapist", "Dentist", "Veterinarian",
    ]),
    "counseling": ("counseling and social work", ["Social Worker", "Therapist", "Counselor"]),
    "education": ("education and research", ["Teacher", "Professor", "Research Scientist", "Postdoctoral Researcher"]),
    "legal": ("law", ["Lawyer", "Attorney", "Paralegal", "Legal Counsel"]),
    "engineering": ("engineering and architecture", ["Architect", "Civil Engineer", "Mechanical Engineer", "Electrical Engineer"]),
    "projects": ("project management", ["Project Manager", "Program Manager", "Scrum Master"]),
    "writing": ("writing and media", ["Journalist", "Editor", "Copywriter", "Content Writer", "Technical Writer"]),
    "real_estate": ("real estate", ["Real Estate Agent", "Property Manager"]),
    "hospitality": ("food and hospitality", ["Chef", "Restaurant Manager"]),
    "aviation": ("aviation", ["Flight Attendant", "Pilot"]),
}

# Keyword fallback for custom titles, checked in order - more specific
# rules first (e.g. "software architect" must hit software before the
# generic "architect" rule).
_KEYWORD_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("software", ("software", "developer", "programmer", "frontend", "backend", "full stack", "fullstack",
                  "devops", "site reliability", "sre", "mobile engineer", "ios", "android", "web engineer")),
    ("data", ("data ", "data", "machine learning", "analytics", " ml ", "ai engineer")),
    ("product", ("product manager", "product owner", "product lead")),
    ("design", ("designer", "design", " ux", "ux ", " ui", "ui ", "illustrator", "photographer", "videographer")),
    ("marketing", ("marketing", "growth", "brand", "seo", "social media", "community")),
    ("sales", ("sales", "account executive", "business development", "customer success", "bdr", "sdr")),
    ("finance", ("finance", "financial", "accountant", "accounting", "controller", "investment", "banker", "banking")),
    ("consulting", ("consultant", "consulting")),
    ("people", ("recruit", "talent", "hr ", "human resources", "people ops", "people operations")),
    ("healthcare", ("nurse", "physician", "doctor", "pharmacist", "physical therapist", "dentist", "veterinar", "surgeon")),
    ("counseling", ("therapist", "counselor", "social worker", "psycholog")),
    ("education", ("teacher", "professor", "lecturer", "researcher", "research scientist", "educator")),
    ("legal", ("lawyer", "attorney", "legal", "paralegal", "counsel")),
    ("engineering", ("civil engineer", "mechanical engineer", "electrical engineer", "structural", "architect")),
    ("projects", ("project manager", "program manager", "scrum")),
    ("writing", ("writer", "editor", "journalist", "reporter", "copywriter")),
    ("real_estate", ("real estate", "realtor", "property manager")),
    ("hospitality", ("chef", "cook", "restaurant", "hospitality", "sommelier")),
    ("aviation", ("pilot", "flight attendant")),
]

# Seniority/level words that don't change what someone actually does
_SENIORITY = {"senior", "sr", "sr.", "staff", "principal", "lead", "junior", "jr", "jr.", "entry-level", "associate"}

_TITLE_TO_FAMILY = {
    title.strip().lower(): family for family, (_, titles) in CAREER_FAMILIES.items() for title in titles
}


def core_role(title: str | None) -> str:
    """'Senior Product Manager' -> 'product manager'. A bare seniority word
    ('Associate', 'Senior Associate') keeps its last word so it isn't
    erased entirely."""
    words = (title or "").strip().lower().split()
    while len(words) > 1 and words[0] in _SENIORITY:
        words = words[1:]
    return " ".join(words)


def core_role_display(title: str | None) -> str:
    """Same as core_role but keeps the original capitalization, for showing
    a shared role that's true for BOTH people: 'Senior Data Scientist'
    matched with 'Data Scientist' is described as 'Data Scientist'."""
    words = (title or "").strip().split()
    while len(words) > 1 and words[0].lower() in _SENIORITY:
        words = words[1:]
    return " ".join(words)


def career_family(title: str | None) -> str | None:
    normalized = (title or "").strip().lower()
    if not normalized:
        return None
    if normalized in _TITLE_TO_FAMILY:
        return _TITLE_TO_FAMILY[normalized]
    if core_role(normalized) in _TITLE_TO_FAMILY:
        return _TITLE_TO_FAMILY[core_role(normalized)]
    padded = f" {normalized} "
    for family, keywords in _KEYWORD_RULES:
        if any(k in padded for k in keywords):
            return family
    return None


def family_phrase(family: str) -> str:
    return CAREER_FAMILIES[family][0]
