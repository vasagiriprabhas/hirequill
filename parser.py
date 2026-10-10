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
    "education": ["education", "academic details", "academics", "qualification", "qualifications"],
    "certifications": ["certifications", "certificates", "courses", "licenses"],
    "achievements": ["achievements", "awards", "accomplishments", "extracurricular", "activities"],
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


def _heading_of(line: str):
    """Return the section name if this line looks like a heading, else None."""
    candidate = re.sub(r"[^a-zA-Z ]", "", line).strip().lower()
    if not candidate or len(candidate.split()) > 4:
        return None
    return _HEADING_LOOKUP.get(candidate)


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


def normalize_for_matching(text: str) -> str:
    """Lowercase, no symbols. Used later for skill matching (Day 2)."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#./ \n]", " ", text)  # keep c++, c#, node.js
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
