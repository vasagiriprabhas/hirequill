"""Day 2 demo: compare a resume PDF against a job description text file (skills only).

Usage:  python day2.py resume.pdf job_description.txt
(Day 3 adds the meaning score and the final score: python day3.py ...)
"""
import sys

from extractor import extract_skills, match_skills, skills_by_section
from parser import parse_resume


def show(title, items):
    print(f"{title} ({len(items)}): " + (", ".join(items) if items else "none"))


def main(resume_pdf, jd_path):
    resume = parse_resume(resume_pdf)
    with open(jd_path, encoding="utf-8", errors="ignore") as f:
        jd_text = f.read()

    resume_skills = extract_skills(resume["clean_text"], expand=True)  # credit implied skills
    result = match_skills(resume_skills, jd_text)  # only what the job literally asks for
    where = skills_by_section(resume["sections"])

    print("=" * 60)
    print(f"SKILL MATCH SCORE: {result['score']}%  "
          f"({len(result['matched'])} of {result['jd_skill_count']} requirements)")
    print("=" * 60)

    print("\nRequirements you meet:")
    for item in result["matched"]:
        print(f"  [+] {item}")
    print("\nWhere your resume shows those skills:")
    for skill in result["matched_skills"]:
        print(f"  {skill:<26} {', '.join(where.get(skill, ['?']))}")

    print()
    show("[-] Missing", result["missing"])
    show("[ ] Extra skills (not asked by this job)", result["extra"])
    print()
    show("Soft skills the job mentions", result["soft_in_jd"])
    show("  ...not visible in your resume", result["soft_missing"])

    if result["jd_skill_count"] == 0:
        print("\nNo skills found in the job description. Is the file empty or too short?")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python day2.py resume.pdf job_description.txt")
    main(sys.argv[1], sys.argv[2])
