"""Day 4: the gap report. What is weak in the resume, what to add, what to learn.

Two layers:
  1. Rule-based (always works, no internet, no key): structure checks, unproven skills,
     missing skills ranked by how often the job mentions them, and a learning plan.
  2. AI suggestions (needs a free API key): rewrites of your own bullets and summary.
     Guard rails stop the AI from inventing experience: anything it adds that is not in
     your resume is flagged "use only if true".
"""
import re
from difflib import SequenceMatcher

from extractor import _PATTERNS, extract_skills, jd_requirements
from llm import LLMUnavailable, ask, parse_json, redact
from parser import normalize_for_matching
from resources import CONCEPT_SKILLS, lookup

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
PLAN_LIMIT = 6  # more than this in one plan is not realistic


# ---------------------------------------------------------------- rule-based layer
def _mentions(skill: str, jd_text: str) -> int:
    return len(_PATTERNS[skill].findall(normalize_for_matching(jd_text)))


def _bullets(text: str) -> list:
    """Lines of a section that are real sentences, not headings or one-word lines."""
    lines = [re.sub(r"^[\s\-*•]+", "", l).strip() for l in text.split("\n")]
    return [l for l in lines if len(l.split()) >= 5]


def _bullet_items(text: str) -> list:
    """Real bullet points. A bullet that wraps onto a second PDF line is joined back together."""
    items, current = [], None
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("-"):
            if current:
                items.append(current)
            current = line.lstrip("-* ").strip()
        elif current is not None and not re.search(r"[.!?]$", current) and len(current) < 300:
            current += " " + line          # continuation of a wrapped bullet
        else:
            if current:
                items.append(current)
            current = None                 # a title line such as a project name
    if current:
        items.append(current)
    items = [i[:300] for i in items if len(i.split()) >= 5]
    return items or _bullets(text)


def missing_requirements(resume_skills: set, jd_text: str) -> list:
    """Missing skills as a list of dicts, most-mentioned first.
    A group like 'AWS or Azure' becomes ONE item, and we suggest the quicker option."""
    singles, groups, _ = jd_requirements(jd_text)
    items = []
    for skill in singles:
        if skill not in resume_skills:
            items.append({"label": skill, "skill": skill, "mentions": _mentions(skill, jd_text),
                          "options": [skill]})
    for group in groups:
        if not (group & resume_skills):
            quickest = min(sorted(group), key=lambda s: lookup(s)[0])
            items.append({"label": f"{quickest} (job accepts any of: {', '.join(sorted(group))})",
                          "skill": quickest, "mentions": max(_mentions(s, jd_text) for s in group),
                          "options": sorted(group)})
    items.sort(key=lambda i: (-i["mentions"], lookup(i["skill"])[0], i["label"]))
    return items


def structure_checks(resume: dict, jd_text: str, resume_skills: set) -> list:
    """Problems we can detect without any AI. Each is {severity, issue, why, fix}."""
    text, sections = resume["clean_text"], resume["sections"]
    found = []

    def add(severity, issue, why, fix):
        found.append({"severity": severity, "issue": issue, "why": why, "fix": fix})

    # Missing sections
    if "projects" not in sections and "experience" not in sections:
        if re.search(r"project|internship", text, re.IGNORECASE):
            add("medium", "I could not find a clearly labelled Projects section",
                "Your resume mentions projects, but not under a heading that recruiter software can recognise. "
                "Those tools read your resume by headings.",
                "Put a heading named exactly PROJECTS (or ACADEMIC PROJECTS) on its own line above your projects.")
        else:
            add("high", "No Projects or Experience section found",
                "For a fresher, projects are the proof of your skills. Without them recruiters have only a list of words.",
                "Add a Projects section with 2-3 projects, each with a one-line goal, the tools used, and a result.")
    if "skills" not in sections:
        add("medium", "No Skills section found",
            "Recruiter tools and ATS software scan for a clear Skills section first.",
            "Add a Skills section grouped like: Languages | Databases | Tools | Cloud.")
    if "summary" not in sections:
        add("low", "No summary at the top",
            "A 2-line summary tells the reader instantly which role you are targeting.",
            "Add 2 lines: your degree, the role you want, and your 3 strongest skills for that role.")
    elif not (extract_skills(sections["summary"]) & extract_skills(jd_text)):
        add("medium", "Your summary does not mention any skill this job asks for",
            "The summary is the first thing read. A generic one wastes it.",
            "Rewrite it for this role: name the role and 2-3 skills from the job description that you really have.")
    if "certifications" not in sections:
        add("low", "No Certifications section found",
            "Certificates help a fresher with no work experience, especially from known platforms.",
            "Add completed courses and certificates, with the platform name (NPTEL, SmartBridge, etc.).")

    # Links
    if not re.search(r"github|linkedin", text, re.IGNORECASE):
        add("medium", "No GitHub or LinkedIn link found",
            "Recruiters want to verify your work. A live link beats a claim.",
            "Add your GitHub and LinkedIn in the header. Link each project to its repo or live demo.")

    # Numbers in project bullets
    work_text = "\n".join(sections.get(k, "") for k in ("projects", "experience"))
    bullets = _bullet_items(work_text)
    if len(bullets) >= 2:
        without_numbers = [b for b in bullets if not re.search(r"\d", b)]
        if len(without_numbers) / len(bullets) >= 0.6:
            example = without_numbers[0][:90]
            add("high", f"{len(without_numbers)} of {len(bullets)} project lines have no numbers",
                "Numbers (rows of data, accuracy, time saved, number of charts) make a claim believable.",
                f'Add a real number to each line. Example line to improve: "{example}"')
    elif 0 <= len(bullets) < 2 and ("projects" in sections or "experience" in sections):
        add("medium", "Your projects are described in very little detail",
            "One short line per project does not show what you actually did.",
            "Use 2-3 lines per project: the problem, what you built (tools), and the result.")

    # Skills listed but never shown in a project
    if "projects" in sections or "experience" in sections:
        proof_text = "\n".join(sections.get(k, "") for k in ("projects", "experience", "certifications", "achievements"))
        explicit = extract_skills(text)
        proven = extract_skills(proof_text, expand=True)  # a Pandas project also proves Python
        singles, groups, _ = jd_requirements(jd_text)
        wanted = set(singles).union(*groups) if groups else set(singles)
        unproven = sorted(s for s in wanted if s in explicit and s not in proven)
        if unproven:
            add("high", f"Skills the job wants appear only in your Skills list: {', '.join(unproven)}",
                "A skill listed without a project that uses it is the first thing an interviewer will test.",
                "Mention each of these inside a project or internship line, for example what you did with it. "
                "If you have not actually used one, either build a small project or take it off the list.")

    # Length
    words = len(text.split())
    if words < 150:
        add("medium", f"Resume looks very short ({words} words)",
            "Too little text gives the reader and the ATS little to match against.",
            "Expand projects and skills with real detail. Keep it to one page.")
    elif words > 800:
        add("low", f"Resume looks long ({words} words)",
            "A fresher resume should fit on one page.", "Cut older or weaker items and shorten long lines.")

    found.sort(key=lambda f: SEVERITY_ORDER[f["severity"]])
    return found


def learning_plan(missing: list, hours_per_week: int = 10) -> dict:
    """Turn the missing skills into an ordered study plan with free resources."""
    chosen = missing[:PLAN_LIMIT]
    steps, total = [], 0
    for item in chosen:
        hours, resources = lookup(item["skill"])
        total += hours
        if item["skill"] in CONCEPT_SKILLS:
            prove = ("This is a concept, not a tool. Prepare one real example (the situation, what you did, what happened) "
                     "from a project, internship or college activity, and add it as one line. Do not claim it without an example.")
        else:
            prove = f"Use {item['skill']} in a small project and add one numbered line about it to your resume."
        steps.append({"skill": item["skill"], "label": item["label"], "hours": hours, "resources": resources,
                      "prove_it": prove})
    weeks = round(total / max(hours_per_week, 1), 1)
    return {"steps": steps, "total_hours": total, "weeks": weeks, "hours_per_week": hours_per_week,
            "skipped": [i["label"] for i in missing[PLAN_LIMIT:]]}


# ---------------------------------------------------------------- AI layer
# Design rule: the AI never quotes your resume. WE pick your real lines and number them;
# the AI only rewrites "line 1, line 2...". So every "Before" is guaranteed to be yours.
SYSTEM_PROMPT = """You are a careful resume coach for an Indian fresher applying for entry-level roles.
STRICT RULES:
1. Use ONLY facts that appear in the text you are given. Never add a tool, skill, project, employer, or number that is not in it.
2. If a number would make a line stronger but the text has none, write a placeholder in square brackets
   such as [N rows] or [X%]. The candidate fills it in only if true.
3. Improve wording only: a stronger action verb, a clearer result, and keywords from the job description that the
   candidate ALREADY has. Keep it to one sentence of similar length.
4. Do not change what a thing is: a dashboard stays a dashboard, a project stays a project. Do not turn it into a
   "tool", "framework" or "system".
5. Do not claim a level: never use the words fluent, expert, proficient, experienced, extensive, advanced or strong.
6. Reply with JSON only, no other text."""

OVERCLAIM_WORDS = ("fluent", "fluency", "expert", "expertise", "proficient", "proficiency", "experienced",
                   "extensive", "advanced", "seasoned", "mastery", "highly skilled", "years of experience")
LINE_LIMIT = 4


def select_lines(resume: dict, jd_text: str, limit: int = LINE_LIMIT) -> list:
    """The weakest REAL project lines: no numbers first, then the most relevant to the job."""
    sections = resume["sections"]
    work = "\n".join(sections.get(k, "") for k in ("projects", "experience"))
    jd_skills = extract_skills(jd_text)
    ranked = []
    for index, item in enumerate(_bullet_items(work)):
        has_number = bool(re.search(r"\d", item))
        relevance = len(extract_skills(item, expand=True) & jd_skills)
        ranked.append(((has_number, -relevance, index), item))
    ranked.sort(key=lambda pair: pair[0])
    return [item for _, item in ranked[:limit]]


def build_prompt(resume: dict, jd_text: str, lines: list, matched: list = None) -> str:
    sections = resume["sections"]
    context = []
    for name in ("summary", "skills", "education", "certifications"):
        if sections.get(name):
            context.append(f"[{name.upper()}]\n{sections[name][:900]}")
    numbered = "\n".join(f"[{i}] {line}" for i, line in enumerate(lines, 1)) or "(none found)"
    return f"""JOB DESCRIPTION:
{redact(jd_text)[:3500]}

CONTEXT FROM THE RESUME (use only for the summary):
{redact(chr(10).join(context))[:3000]}

LINES TO IMPROVE (copied from the resume):
{redact(numbered)}

Return JSON with exactly these keys:
{{
  "summary_rewrite": "2 short lines for a fresher, naming the target role from the job description if it is clear, using only the degree, skills and projects shown above",
  "line_rewrites": [
    {{"id": 1, "improved": "stronger version of line [1], same facts", "why": "one short reason",
      "question": "one question the candidate should answer to add a REAL detail, such as a number or a result"}}
  ]
}}
Give one entry in line_rewrites for each numbered line, using its id number. Do not invent lines."""


_NUMBER = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")


def _novel_numbers(improved: str, resume_text: str) -> list:
    outside_brackets = re.sub(r"\[[^\]]*\]", " ", improved)
    known = set(_NUMBER.findall(resume_text))
    return sorted({n for n in _NUMBER.findall(outside_brackets) if n not in known})


def _flags_for(text: str, resume_text: str, known_skills: set) -> list:
    """Anything in the AI's text that your resume does not back up."""
    flags = []
    new_skills = sorted(extract_skills(text) - known_skills)
    if new_skills:
        flags.append(f"mentions skills not in your resume ({', '.join(new_skills)})")
    new_numbers = _novel_numbers(text, resume_text)
    if new_numbers:
        flags.append(f"contains numbers not in your resume ({', '.join(new_numbers)})")
    lowered, resume_lower = text.lower(), resume_text.lower()
    claims = [w for w in OVERCLAIM_WORDS if w in lowered and w not in resume_lower]
    if claims:
        flags.append(f"claims a level you did not state ({', '.join(claims)})")
    return flags


def check_ai_output(raw: dict, resume: dict, lines: list) -> dict:
    """Keep only well-formed items, attach OUR real line as the 'Before', and flag unbacked claims."""
    resume_text = resume["clean_text"]
    known_skills = extract_skills(resume_text, expand=True)
    clean = {"summary_rewrite": None, "bullet_rewrites": [], "removed_unverified": 0}

    summary = raw.get("summary_rewrite")
    if isinstance(summary, str) and summary.strip():
        clean["summary_rewrite"] = {"text": summary.strip(), "flags": _flags_for(summary, resume_text, known_skills)}

    seen = set()
    for item in (raw.get("line_rewrites") or []):
        if not (isinstance(item, dict) and isinstance(item.get("improved"), str) and item["improved"].strip()):
            continue
        try:
            line_id = int(item.get("id"))
        except (TypeError, ValueError):
            line_id = 0
        if not 1 <= line_id <= len(lines) or line_id in seen:
            clean["removed_unverified"] += 1    # the AI referred to a line that does not exist
            continue
        seen.add(line_id)
        improved = item["improved"].strip()
        if normalize_for_matching(improved) == normalize_for_matching(lines[line_id - 1]):
            continue                            # no real change, nothing to show
        clean["bullet_rewrites"].append({
            "original": lines[line_id - 1],
            "improved": improved,
            "why": str(item.get("why", "")).strip(),
            "question": str(item.get("question", "")).strip(),
            "flags": _flags_for(improved, resume_text, known_skills),
        })
    return clean


def ai_suggestions(resume: dict, jd_text: str, matched: list = None, ask_fn=ask) -> dict:
    """Returns {'ok': True, **suggestions} or {'ok': False, 'note': why it did not run}."""
    lines = select_lines(resume, jd_text)
    try:
        reply = ask_fn(build_prompt(resume, jd_text, lines, matched), system=SYSTEM_PROMPT, want_json=True)
        result = check_ai_output(parse_json(reply), resume, lines)
        if not (result["summary_rewrite"] or result["bullet_rewrites"]):
            note = "The AI returned no usable suggestions. Try again."
            if result["removed_unverified"]:
                note = (f"The AI referred to {result['removed_unverified']} line(s) that do not exist, "
                        "so I removed them. Try again.")
            return {"ok": False, "note": note}
        return {"ok": True, **result}
    except LLMUnavailable as error:
        return {"ok": False, "note": str(error)}
    except ValueError:  # bad JSON from the model
        return {"ok": False, "note": "The AI answered in an unexpected format. Try again."}


# ---------------------------------------------------------------- put it together
def build_report(resume: dict, jd_text: str, use_ai: bool = True, hours_per_week: int = 10, ask_fn=ask,
                 keep_ai_input: bool = False) -> dict:
    resume_skills = extract_skills(resume["clean_text"], expand=True)
    missing = missing_requirements(resume_skills, jd_text)
    singles, groups, soft = jd_requirements(jd_text)
    wanted = set(singles).union(*groups) if groups else set(singles)
    matched = sorted(wanted & resume_skills)

    report = {
        "weak_points": structure_checks(resume, jd_text, resume_skills),
        "missing": missing,
        "soft_missing": sorted(soft - resume_skills),
        "plan": learning_plan(missing, hours_per_week),
        "ai": None,
    }
    if use_ai:
        report["ai"] = ai_suggestions(resume, jd_text, matched, ask_fn)
        if keep_ai_input:
            report["ai_input"] = build_prompt(resume, jd_text, select_lines(resume, jd_text), matched)
    return report


def format_report(report: dict) -> str:
    """Plain-text version for the terminal. The web app (Day 6) will render the same dict."""
    out = []
    icon = {"high": "[!!!]", "medium": "[!!]", "low": "[!]"}

    out.append("WEAK POINTS IN YOUR RESUME (fix the top ones first)")
    out.append("-" * 60)
    if not report["weak_points"]:
        out.append("No structural problems found.")
    for i, w in enumerate(report["weak_points"], 1):
        out += [f"{i}. {icon[w['severity']]} {w['issue']}", f"   Why it matters: {w['why']}", f"   Fix: {w['fix']}", ""]

    out.append("SKILLS THE JOB WANTS THAT YOUR RESUME DOES NOT SHOW")
    out.append("-" * 60)
    if report["missing"]:
        for m in report["missing"]:
            out.append(f"  - {m['label']}  (job mentions it {m['mentions']}x)")
    else:
        out.append("  None. You cover every skill this job lists.")
    if report["soft_missing"]:
        out.append(f"  Soft skills to show with examples: {', '.join(report['soft_missing'])}")

    plan = report["plan"]
    out += ["", "LEARNING PLAN (free resources)", "-" * 60]
    if not plan["steps"]:
        out.append("  Nothing to learn for this job.")
    for i, s in enumerate(plan["steps"], 1):
        out.append(f"{i}. {s['label']}  (about {s['hours']} hours)")
        for r in s["resources"]:
            out.append(f"     - {r}")
        out.append(f"     Then: {s['prove_it']}")
    if plan["steps"]:
        out.append(f"\n  Total: about {plan['total_hours']} hours = {plan['weeks']} weeks at {plan['hours_per_week']} hours/week.")
    if plan["skipped"]:
        out.append(f"  Later (not in this plan): {', '.join(plan['skipped'])}")

    out += ["", "AI SUGGESTIONS", "-" * 60]
    ai = report["ai"]
    if ai is None:
        out.append("  Turned off.")
    elif not ai["ok"]:
        out.append(f"  Not available: {ai['note']}")
        out.append("  (The rule-based report above still works without AI.)")
    else:
        if ai["summary_rewrite"]:
            s_ = ai["summary_rewrite"]
            out += ["Suggested summary:", f"  {s_['text']}"]
            out += [f"  ** CHECK: {f}. Use only if true. **" for f in s_["flags"]]
        if ai["bullet_rewrites"]:
            out.append("\nYour weakest real lines, rewritten:")
        for b in ai["bullet_rewrites"]:
            out += ["", f"Before: {b['original']}", f"After:  {b['improved']}"]
            if b["why"]:
                out.append(f"Why:    {b['why']}")
            if b["question"]:
                out.append(f"Add a real detail: {b['question']}")
            out += [f"  ** CHECK: {f}. Use only if true. **" for f in b["flags"]]
        if ai.get("removed_unverified"):
            out += ["", f"  Removed {ai['removed_unverified']} suggestion(s): the AI referred to lines that do not exist."]
        out.append("\nReplace any [bracketed] placeholder with a real number, or delete it.")
    return "\n".join(out)
