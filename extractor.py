"""Day 2: find skills in a resume and a job description, then compare them."""
import re

from parser import normalize_for_matching
from skills import IMPLIES, SKILLS

SOFT = "soft_skills"


def _build_patterns():
    """One compiled regex per skill. Boundaries stop 'java' matching inside 'javascript'
    and 'sql' matching inside 'mysql', while still allowing c++, c#, node.js, ci/cd."""
    patterns, category_of = {}, {}
    for category, skills in SKILLS.items():
        for canonical, aliases in skills.items():
            if canonical in category_of:
                raise ValueError(f"Duplicate skill in skills.py: {canonical}")
            category_of[canonical] = category
            names = {normalize_for_matching(n) for n in [canonical, *aliases]}
            names = sorted(names, key=len, reverse=True)  # longest first
            alternatives = "|".join(re.escape(n) for n in names)
            patterns[canonical] = re.compile(
                r"(?<![a-z0-9+#])(?:" + alternatives + r")(?![a-z0-9+#])"
            )
    return patterns, category_of


_PATTERNS, CATEGORY_OF = _build_patterns()


def extract_skills(text: str, expand: bool = False) -> set:
    """Return the set of canonical skills found in the text.

    expand=True also adds implied skills (MySQL -> SQL, Tableau -> dashboards).
    Use it for RESUMES, so a candidate gets credit for what their skills imply.
    Do not use it for JOB DESCRIPTIONS, or we would invent requirements the job
    never asked for.
    """
    cleaned = normalize_for_matching(text)
    found = {skill for skill, pattern in _PATTERNS.items() if pattern.search(cleaned)}
    if expand:
        for skill in list(found):
            found.update(IMPLIES.get(skill, []))
    return found


def skills_by_section(sections: dict) -> dict:
    """Which resume sections mention each skill? {skill: [section, ...]}"""
    where = {}
    for section_name, body in sections.items():
        for skill in extract_skills(body, expand=True):
            where.setdefault(skill, []).append(section_name)
    return where


def compare(resume_skills: set, jd_skills: set) -> dict:
    """Compare what the resume has against what the job asks for.

    The score uses technical and domain skills only. Soft skills (communication,
    teamwork) are listed separately because they are easy to claim and hard to test.
    """
    jd_tech = {s for s in jd_skills if CATEGORY_OF[s] != SOFT}
    jd_soft = {s for s in jd_skills if CATEGORY_OF[s] == SOFT}

    matched = sorted(jd_tech & resume_skills)
    missing = sorted(jd_tech - resume_skills)
    score = round(100 * len(matched) / len(jd_tech), 1) if jd_tech else 0.0

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
        "extra": sorted(s for s in resume_skills - jd_skills if CATEGORY_OF[s] != SOFT),
        "soft_in_jd": sorted(jd_soft),
        "soft_matched": sorted(jd_soft & resume_skills),
        "soft_missing": sorted(jd_soft - resume_skills),
        "jd_skill_count": len(jd_tech),
    }
