"""Day 4 demo: score + gap report for a resume PDF against a job description.

Usage:
    python day4.py resume.pdf job_description.txt            (AI on if an API key is set)
    python day4.py resume.pdf job_description.txt --no-ai    (rule-based report only)
    python day4.py resume.pdf job_description.txt --hours 15 (study hours per week, default 10)
    python day4.py resume.pdf job_description.txt --show-ai-input   (print exactly what is sent to the AI)
"""
import sys

from extractor import extract_skills, match_skills
from gap_report import build_report, format_report
from parser import parse_resume
from scorer import final_score, meaning_score


def main(resume_pdf, jd_path, use_ai=True, hours=10, show_input=False):
    resume = parse_resume(resume_pdf)
    with open(jd_path, encoding="utf-8", errors="ignore") as f:
        jd_text = f.read()

    skills = match_skills(extract_skills(resume["clean_text"], expand=True), jd_text)
    meaning = meaning_score(resume["clean_text"], jd_text)
    final = final_score(skills["score"], meaning["score"])

    print("=" * 62)
    print(f"FINAL MATCH SCORE: {final['score']}%   [{final['band'].upper()}]   {final['advice']}")
    print("=" * 62 + "\n")
    report = build_report(resume, jd_text, use_ai=use_ai, hours_per_week=hours, keep_ai_input=show_input)
    print(format_report(report))
    if show_input and report.get("ai_input"):
        print("\n" + "=" * 62 + "\nTEXT SENT TO THE AI (email, phone and links already removed)\n" + "=" * 62)
        print(report["ai_input"])


if __name__ == "__main__":
    args = sys.argv[1:]
    use_ai = "--no-ai" not in args
    show_input = "--show-ai-input" in args
    hours = 10
    if "--hours" in args:
        hours = int(args[args.index("--hours") + 1])
        del args[args.index("--hours"):args.index("--hours") + 2]
    args = [a for a in args if a not in ("--no-ai", "--show-ai-input")]
    if len(args) != 2:
        sys.exit(__doc__)
    main(args[0], args[1], use_ai, hours, show_input)
