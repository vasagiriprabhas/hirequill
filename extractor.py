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


def _non_overlapping_spans(cleaned: str) -> list:
    """Every skill mention as (start, end, skill). If two overlap, keep the longer."""
    raw = [(m.start(), m.end(), skill)
           for skill, pattern in _PATTERNS.items()
           for m in pattern.finditer(cleaned)]
    raw.sort(key=lambda span: (span[0], -(span[1] - span[0])))
    spans, last_end = [], -1
    for start, end, skill in raw:
        if start >= last_end:
            spans.append((start, end, skill))
            last_end = end
    return spans


def _gap_kind(gap: str):
    """What sits between two skill mentions? ', ' and '/' = both needed. 'or' = either."""
    g = gap.strip()
    if g in (",", "/"):
        return "and"
    if re.fullmatch(r",?\s*(?:and/)?or", g):
        return "or"
    return None


def jd_requirements(jd_text: str):
    """Work out what a job description really asks for.

    Returns (singles, groups, soft):
      singles - skills that are each required
      groups  - sets of alternatives where ONE is enough ("Tableau, Power BI or Qlik")
      soft    - soft skills mentioned (listed, but not scored)

    Alternatives are only grouped when they share a category, so
    "Python, SQL, Tableau or Power BI" groups Tableau with Power BI, not with SQL.
    Limitation: "Python, SQL or R" groups all three, since they share a category.
    """
    cleaned = normalize_for_matching(jd_text, keep_commas=True)
    spans = _non_overlapping_spans(cleaned)

    chains = []  # each chain: list of (skill, how it joins the previous skill)
    prev = None
    for start, end, skill in spans:
        kind = _gap_kind(cleaned[prev[1]:start]) if prev else None
        joins = (
            kind
            and CATEGORY_OF[skill] == CATEGORY_OF[prev[2]]
            and CATEGORY_OF[skill] != SOFT
        )
        if joins:
            chains[-1].append((skill, kind))
        else:
            chains.append([(skill, None)])
        prev = (start, end, skill)

    singles, groups, soft = set(), [], set()
    for chain in chains:
        skills = [s for s, _ in chain]
        if CATEGORY_OF[skills[0]] == SOFT:
            soft.update(skills)
        elif any(kind == "or" for _, kind in chain) and len(set(skills)) > 1:
            group = frozenset(skills)
            if group not in groups:
                groups.append(group)
        else:
            singles.update(skills)
    return singles, groups, soft


def match_skills(resume_skills: set, jd_text: str) -> dict:
    """Compare what the resume has against what the job asks for.

    Every single skill and every "any one of these" group counts as one requirement.
    Soft skills (communication, teamwork) are listed but not scored, because they
    are easy to claim and hard to test.
    """
    singles, groups, soft = jd_requirements(jd_text)

    matched, matched_skills, missing = [], [], []
    for skill in sorted(singles):
        if skill in resume_skills:
            matched.append(skill)
            matched_skills.append(skill)
        else:
            missing.append(skill)
    for group in groups:
        hits = sorted(group & resume_skills)
        if hits:
            matched.append(f"{', '.join(hits)}  (job accepts any of: {', '.join(sorted(group))})")
            matched_skills.extend(hits)
        else:
            missing.append(f"any one of: {', '.join(sorted(group))}")

    total = len(singles) + len(groups)
    score = round(100 * len(matched) / total, 1) if total else 0.0
    asked = set(singles).union(*groups) if groups else set(singles)

    return {
        "score": score,
        "matched": matched,
        "matched_skills": matched_skills,
        "missing": missing,
        "extra": sorted(s for s in resume_skills - asked - soft if CATEGORY_OF[s] != SOFT),
        "soft_in_jd": sorted(soft),
        "soft_matched": sorted(soft & resume_skills),
        "soft_missing": sorted(soft - resume_skills),
        "jd_skill_count": total,
    }
