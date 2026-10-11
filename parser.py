"""Day 1: read a resume PDF, clean the text, and split it into sections."""
import re
import sys

import pdfplumber

# Heading words we look for. A line counts as a heading only if it is short
# and matches one of these (so a sentence containing "skills" is not a heading).
SECTION_HEADINGS = {
    "summary": ["summary", "objective", "profile", "career objective", "professional summary"],
    "skills": ["skills", "technical skills", "key skills", "core skills", "technologies"],
    "projects": ["projects", "academic projects", "personal projects", "project work"],
    "experience": ["experience", "work experience", "internships", "internship", "professional experience"],
    "education": ["education", "academic details", "academics", "qualification", "qualifications", "academic qualification",
                  "academic qualifications", "educational qualification", "educational qualifications", "education details"],
    "certifications": ["certifications", "certificates", "courses", "licenses"],
    "languages": ["languages", "language skills", "languages known"],
    "interests": ["interests", "hobbies", "hobbies and interests", "interests and hobbies", "hobbies interests", "interests hobbies"],
    "achievements": ["leadership", "leadership and extracurricular", "extracurricular activities", "achievements", "awards", "accomplishments", "extracurricular", "activities"],
}

# Reverse lookup: "technical skills" -> "skills"
_HEADING_LOOKUP = {
    alias: section for section, aliases in SECTION_HEADINGS.items() for alias in aliases
}


def extract_text(pdf_path: str) -> str:
    """Pull raw text out of every page of the PDF."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    text = "\n".join(pages).strip()
    if not text:
        raise ValueError(
            "No text found. The PDF may be a scanned image; "
            "export your resume from Word/Docs as a text PDF instead."
        )
    return text


def clean_text(text: str) -> str:
    """Tidy raw text but keep line breaks (we need them to find headings)."""
    text = text.replace("•", "-").replace("●", "-").replace("–", "-")
    text = re.sub(r"[ \t]+", " ", text)          # collapse spaces/tabs
    text = re.sub(r"\n\s*\n+", "\n", text)       # drop blank lines
    return "\n".join(line.strip() for line in text.split("\n")).strip()


# Keywords for headings that are not in the exact list above, e.g. "Project Experience",
# "Technical Projects", "Internships & Projects". Checked in this order.
_FUZZY = [
    ("project", "projects"), ("intern", "experience"), ("experience", "experience"),
    ("skill", "skills"), ("technolog", "skills"), ("education", "education"),
    ("academic", "education"), ("qualification", "education"), ("certif", "certifications"), ("achievement", "achievements"),
    ("award", "achievements"), ("leadership", "achievements"), ("extracurricular", "achievements"),
    ("summary", "summary"), ("objective", "summary"), ("profile", "summary"),
]


def _heading_of(line: str):
    """Return the section name if this line looks like a heading, else None.

    Exact names first ("Technical Skills"). Then a looser match for short lines that
    LOOK like headings: ALL CAPS, ending with ':', or ending in the keyword itself.
    A project title like "Skills Gap Analyzer" is not treated as a heading.
    """
    letters = re.sub(r"[^a-zA-Z ]", "", line).strip()
    words = letters.lower().split()
    if len(words) > 2 and all(len(w) == 1 for w in words):   # "P R O J E C T S"
        words = ["".join(words)]
    if not words or len(words) > 6:
        return None
    exact = _HEADING_LOOKUP.get(" ".join(words))
    if exact:
        return exact
    if len(words) > 4:
        return None
    has_connector = bool(re.search(r"&|\band\b", line, re.IGNORECASE))
    keyword_at_end = any(words[-1].startswith(k) for k, _ in _FUZZY)
    keyword_at_start = has_connector and any(words[0].startswith(k) for k, _ in _FUZZY)
    looks_like_heading = letters.isupper() or line.rstrip().endswith(":") or keyword_at_end or keyword_at_start
    if not looks_like_heading:
        return None
    for keyword, section in _FUZZY:
        if any(keyword in w for w in words):
            return section
    return None


def split_sections(text: str) -> dict:
    """Group the resume lines under their headings."""
    sections = {"header": []}
    current = "header"
    for line in text.split("\n"):
        heading = _heading_of(line)
        if heading:
            current = heading
            sections.setdefault(current, [])
        else:
            sections[current].append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items() if lines}


def normalize_for_matching(text: str, keep_commas: bool = False) -> str:
    """Lowercase, no symbols. Used for skill matching.

    keep_commas=True is used when reading job descriptions, so we can tell the
    difference between "Python, SQL" (both needed) and "Tableau or Power BI".
    """
    text = text.lower()
    allowed = r"[^a-z0-9+#./, \n]" if keep_commas else r"[^a-z0-9+#./ \n]"
    text = re.sub(allowed, " ", text)  # keep c++, c#, node.js
    return re.sub(r"\s+", " ", text).strip()


def parse_resume(pdf_path: str) -> dict:
    raw = extract_text(pdf_path)
    cleaned = clean_text(raw)
    return {
        "raw_text": raw,
        "clean_text": cleaned,
        "match_text": normalize_for_matching(cleaned),
        "sections": split_sections(cleaned),
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python parser.py path/to/resume.pdf")
    result = parse_resume(sys.argv[1])
    print(f"Found sections: {', '.join(result['sections'])}\n")
    for name, body in result["sections"].items():
        print(f"=== {name.upper()} ===\n{body}\n")
