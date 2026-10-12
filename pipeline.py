"""Day 6: the glue between the Day 1-5 code and the web page.

No Streamlit in this file, so everything here can be tested on its own (see test_app_logic.py).
  - resume_from_pdf / resume_from_text : safe ways to get a resume into the app
  - analyze                            : skills score + meaning score + final score + band
  - AiBudget                           : a per-visitor cap on AI calls, so a public demo cannot burn the free quota
"""
import hashlib
import io
import os

import pdfplumber

from extractor import extract_skills, match_skills, skills_by_section
from llm import LLMUnavailable
from parser import clean_text, normalize_for_matching, parse_resume, split_sections
from scorer import final_score, meaning_score

MAX_PDF_MB = 5
MAX_PAGES = 6
MAX_JD_CHARS = 12000
MIN_JD_WORDS = 25
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
def clean_jd(jd_text: str) -> str:
    text = (jd_text or "").strip()
    if not text:
        raise InputProblem("Paste the job description first.")
    return text[:MAX_JD_CHARS]


def jd_key(jd_text: str) -> str:
    """Short fingerprint, so we only compare scores across tries for the SAME job."""
    return hashlib.sha1(normalize_for_matching(jd_text).encode()).hexdigest()[:10]


def analyze(resume: dict, jd_text: str, backend: str = None) -> dict:
    jd = clean_jd(jd_text)
    resume_skills = extract_skills(resume["clean_text"], expand=True)
    skills = match_skills(resume_skills, jd)
    meaning = meaning_score(resume["clean_text"], jd, backend=backend or BACKEND)
    final = final_score(skills["score"], meaning["score"])

    warnings = []
    if len(jd.split()) < MIN_JD_WORDS:
        warnings.append("The job description is very short, so the score may not mean much. "
                        "Paste the full text, including the skills and responsibilities.")
    if skills["jd_skill_count"] == 0:
        warnings.append("I could not recognise any skills in that job description. "
                        "Check that you pasted the right text.")
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
class AiBudget:
    """Counts AI calls for one visitor. Past the limit, the AI is refused politely and the app
    carries on with its rule-based report and keyword-estimate scoring."""

    def __init__(self, limit: int = DEFAULT_AI_LIMIT):
        self.limit = limit
        self.used = 0

    @property
    def remaining(self) -> int:
        return max(self.limit - self.used, 0)

    def wrap(self, ask_fn):
        def guarded(*args, **kwargs):
            if self.used >= self.limit:
                raise LLMUnavailable("This visit has used its free AI allowance. "
                                     "The rule-based report and estimated scores still work.")
            self.used += 1
            return ask_fn(*args, **kwargs)
        return guarded
