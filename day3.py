"""Day 3 demo: full match score for a resume PDF against a job description.

Usage:  python day3.py resume.pdf job_description.txt
"""
import sys

from extractor import extract_skills, match_skills, skills_by_section
from parser import parse_resume
from scorer import final_score, meaning_score


def show(title, items):
    print(f"{title} ({len(items)}): " + (", ".join(items) if items else "none"))


def main(resume_pdf, jd_path):
    resume = parse_resume(resume_pdf)
    with open(jd_path, encoding="utf-8", errors="ignore") as f:
        jd_text = f.read()

    resume_skills = extract_skills(resume["clean_text"], expand=True)
    skills = match_skills(resume_skills, jd_text)
    meaning = meaning_score(resume["clean_text"], jd_text)
    final = final_score(skills["score"], meaning["score"])
    where = skills_by_section(resume["sections"])

    print("=" * 62)
    print(f"FINAL MATCH SCORE: {final['score']}%   [{final['band'].upper()}]")
    print(f"  Skills match:  {skills['score']}%  ({len(skills['matched'])} of "
          f"{skills['jd_skill_count']} requirements)   weight 60%")
    print(f"  Meaning match: {meaning['score']}%  (method: {meaning['backend']}, "
          f"{meaning['lines_checked']} job lines checked)   weight 40%")
    print(f"  Next step: {final['advice']}")
    print("=" * 62)
    if meaning["note"]:
        print(f"Note: {meaning['note']}")

    print("\nRequirements you meet:")
    for item in skills["matched"]:
        print(f"  [+] {item}")
    print("\nWhere your resume shows those skills:")
    for skill in skills["matched_skills"]:
        print(f"  {skill:<26} {', '.join(where.get(skill, ['?']))}")

    print()
    show("[-] Missing", skills["missing"])
    show("[ ] Extra skills (not asked by this job)", skills["extra"])
    print()
    show("Soft skills the job mentions", skills["soft_in_jd"])
    show("  ...not visible in your resume", skills["soft_missing"])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python day3.py resume.pdf job_description.txt")
    main(sys.argv[1], sys.argv[2])
