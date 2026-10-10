"""Day 2 demo: compare a resume PDF against a job description text file.

Usage:  python day2.py resume.pdf job_description.txt
"""
import sys

from extractor import compare, extract_skills, skills_by_section
from parser import parse_resume


def show(title, items):
    print(f"{title} ({len(items)}): " + (", ".join(items) if items else "none"))


def main(resume_pdf, jd_path):
    resume = parse_resume(resume_pdf)
    with open(jd_path, encoding="utf-8", errors="ignore") as f:
        jd_text = f.read()

    resume_skills = extract_skills(resume["clean_text"], expand=True)  # credit implied skills
    jd_skills = extract_skills(jd_text)  # only what the job literally asks for
    result = compare(resume_skills, jd_skills)
    where = skills_by_section(resume["sections"])

    print("=" * 60)
    print(f"SKILL MATCH SCORE: {result['score']}%  "
          f"({len(result['matched'])} of {result['jd_skill_count']} required skills)")
    print("=" * 60)

    print("\nMatched skills (and where your resume shows them):")
    for skill in result["matched"]:
        sections = ", ".join(where.get(skill, ["?"]))
        print(f"  [+] {skill:<28} found in: {sections}")

    print()
    show("[-] Missing skills", result["missing"])
    show("[ ] Extra skills (not asked by this JD)", result["extra"])
    print()
    show("Soft skills the JD mentions", result["soft_in_jd"])
    show("  ...your resume shows", result["soft_matched"])
    show("  ...not visible in your resume", result["soft_missing"])

    if not jd_skills:
        print("\nNo skills found in the job description. Is the file empty or too short?")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python day2.py resume.pdf job_description.txt")
    main(sys.argv[1], sys.argv[2])
