"""Day 6: the glue between the Day 1-5 code and the web page.

No Streamlit in this file, so everything here can be tested on its own (see test_app_logic.py).
  - resume_from_pdf / resume_from_text : safe ways to get a resume into the app
  - analyze                            : skills score + meaning score + final score + band
  - AiBudget                           : a per-visitor cap on AI calls, so a public demo cannot burn the free quota
"""
import hashlib
import io
import os
import re
import threading
import time

import pdfplumber

from extractor import extract_skills, match_skills, skills_by_section
from llm import LLMUnavailable
from parser import clean_text, normalize_for_matching, parse_resume, split_sections
from scorer import final_score, meaning_score

MAX_PDF_MB = 5
MAX_PAGES = 6
MAX_JD_CHARS = 12000
MIN_JD_WORDS = 25
MIN_SKILLS_FOR_FULL_WEIGHT = 4
DEFAULT_AI_LIMIT = int(os.environ.get("HIREQUILL_AI_LIMIT", "40"))
BACKEND = os.environ.get("HIREQUILL_BACKEND", "auto")     # "tfidf" = lighter, for small free hosts


class InputProblem(Exception):
    """Something the visitor can fix. The message is shown to them as it is."""


# ---------------------------------------------------------------- getting a resume in
def resume_from_text(text: str) -> dict:
    cleaned = clean_text(text)
    return {"raw_text": text, "clean_text": cleaned, "match_text": normalize_for_matching(cleaned),
            "sections": split_sections(cleaned)}


def resume_from_pdf(data: bytes) -> dict:
    """Read an uploaded PDF fully in memory (nothing is written to disk)."""
    if not data:
        raise InputProblem("That file is empty. Please upload your resume as a PDF.")
    if len(data) > MAX_PDF_MB * 1024 * 1024:
        raise InputProblem(f"That PDF is larger than {MAX_PDF_MB} MB. A resume is normally well under 1 MB.")
    if not data.startswith(b"%PDF"):
        raise InputProblem("That does not look like a PDF file. Please export your resume as a PDF.")
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages = len(pdf.pages)
    except Exception:
        raise InputProblem("I could not open that PDF. If it is password-protected or damaged, export it again.")
    if pages > MAX_PAGES:
        raise InputProblem(f"That PDF has {pages} pages. A fresher resume should be one or two pages "
                           f"(the limit here is {MAX_PAGES}).")
    try:
        return parse_resume(io.BytesIO(data))
    except ValueError as error:             # parse_resume says so when the PDF is only a picture
        raise InputProblem(str(error))
    except Exception:
        raise InputProblem("I could not read the text in that PDF. Export it from Word or Google Docs "
                           "as a text PDF (not a scan or a photo).")


# ---------------------------------------------------------------- scoring
# Job sites add a block of labels (Role, Department, Education...) that describe the listing, not the job.
# "Department: Engineering - Software & QA" would otherwise be read as a "quality assurance" requirement.
_LISTING_LABELS = re.compile(
    r"^\s*(role|industry type|department|employment type|role category|ug|pg|disclaimer|education|"
    r"years of experience)\s*:?.*$", re.IGNORECASE)


def strip_listing_labels(text: str) -> str:
    kept = [line for line in text.splitlines() if not _LISTING_LABELS.match(line)]
    return "\n".join(kept).strip()


def clean_jd(jd_text: str) -> str:
    text = (jd_text or "").strip()
    if not text:
        raise InputProblem("Paste the job description first.")
    stripped = strip_listing_labels(text)
    return (stripped if len(stripped.split()) >= 5 else text)[:MAX_JD_CHARS]


def jd_key(jd_text: str) -> str:
    """Short fingerprint, so we only compare scores across tries for the SAME job."""
    return hashlib.sha1(normalize_for_matching(jd_text).encode()).hexdigest()[:10]


def analyze(resume: dict, jd_text: str, backend: str = None) -> dict:
    jd = clean_jd(jd_text)
    resume_skills = extract_skills(resume["clean_text"], expand=True)
    skills = match_skills(resume_skills, jd)
    meaning = meaning_score(resume["clean_text"], jd, backend=backend or BACKEND)
    # A job text that names only 0-3 recognisable skills gives a skills score built on very little evidence
    # (100% of one skill is not a strong match). Count that part in proportion to the evidence we have.
    evidence = min(skills["jd_skill_count"], MIN_SKILLS_FOR_FULL_WEIGHT) / MIN_SKILLS_FOR_FULL_WEIGHT
    final = final_score(skills["score"] * evidence, meaning["score"])

    warnings = []
    if len(jd.split()) < MIN_JD_WORDS:
        warnings.append("The job description is very short, so the score may not mean much. "
                        "Paste the full text, including the skills and responsibilities.")
    if skills["jd_skill_count"] == 0:
        warnings.append("I could not recognise any skills in that job description. "
                        "Check that you pasted the right text.")
    elif skills["jd_skill_count"] < 3:
        warnings.append(f"Only {skills['jd_skill_count']} skill(s) were recognised in this job description, so the skills "
                        "part of the score counts for less. Treat the score as a rough guide.")
    if len(resume["clean_text"].split()) < 60:
        warnings.append("Very little text was found in your resume. Check that the PDF is not a scan.")

    return {"jd": jd, "jd_key": jd_key(jd), "skills": skills, "meaning": meaning, "final": final,
            "resume_skills": resume_skills, "where": skills_by_section(resume["sections"]),
            "warnings": warnings}


def history_entry(label: str, analysis: dict) -> dict:
    return {"label": label, "final": analysis["final"]["score"], "skills": analysis["skills"]["score"],
            "meaning": analysis["meaning"]["score"], "jd_key": analysis["jd_key"]}


def score_change(history: list):
    """Change in the final score since the previous try, or None if there is no comparable earlier try
    (first try, or a different job description)."""
    if len(history) < 2 or history[-1]["jd_key"] != history[-2]["jd_key"]:
        return None
    return round(history[-1]["final"] - history[-2]["final"], 1)


def default_view(band: str) -> str:
    """High match goes straight to the interview; everyone else starts with what to fix."""
    return "Mock interview" if band == "high" else "Gap report"


# ---------------------------------------------------------------- protecting the free AI quota
DAILY_AI_LIMIT = int(os.environ.get("HIREQUILL_DAILY_AI", "600"))     # all visitors together, per day
AI_COOLDOWN_SECONDS = float(os.environ.get("HIREQUILL_AI_COOLDOWN", "3"))


class DailyGuard:
    """One shared counter for ALL visitors, so a public demo cannot use up the free API quota in a day.
    The app keeps one of these for the whole server (st.cache_resource). It resets each UTC day."""

    def __init__(self, limit: int = DAILY_AI_LIMIT, today=None):
        self.limit = limit
        self._today = today or (lambda: time.strftime("%Y-%m-%d", time.gmtime()))
        self._day, self.used = self._today(), 0
        self._lock = threading.Lock()

    def take(self) -> bool:
        with self._lock:
            if self._today() != self._day:
                self._day, self.used = self._today(), 0
            if self.used >= self.limit:
                return False
            self.used += 1
            return True


class AiBudget:
    """Counts AI calls for one visitor. Past the limit (or while cooling down, or when the whole site has
    used its daily quota) the AI is refused politely and the app carries on with its rule-based report
    and keyword-estimate scoring."""

    def __init__(self, limit: int = DEFAULT_AI_LIMIT, cooldown: float = AI_COOLDOWN_SECONDS,
                 shared: DailyGuard = None, clock=time.monotonic):
        self.limit = limit
        self.used = 0
        self.cooldown = cooldown
        self.shared = shared
        self._clock = clock
        self._last = None

    @property
    def remaining(self) -> int:
        return max(self.limit - self.used, 0)

    def wrap(self, ask_fn):
        def guarded(*args, **kwargs):
            if self.used >= self.limit:
                raise LLMUnavailable("This visit has used its free AI allowance. "
                                     "The rule-based report and estimated scores still work.")
            now = self._clock()
            if self._last is not None and now - self._last < self.cooldown:
                raise LLMUnavailable("Please wait a few seconds before the next AI request, then try again.")
            if self.shared is not None and not self.shared.take():
                raise LLMUnavailable("The AI is very busy today (the free quota is used up). "
                                     "Try again tomorrow; the rule-based report and estimated scores still work.")
            self._last = now
            self.used += 1
            return ask_fn(*args, **kwargs)
        return guarded
