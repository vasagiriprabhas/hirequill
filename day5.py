"""Day 5 demo: mock interview based on your resume and a job description.

Usage:
    python day5.py resume.pdf job_description.txt              (AI on if an API key is set)
    python day5.py resume.pdf job_description.txt --no-ai      (keyword-based scoring only)
    python day5.py resume.pdf job_description.txt --questions 5
    python day5.py resume.pdf job_description.txt --preview    (only list the questions, no interview)
"""
import sys

from extractor import extract_skills, match_skills
from interview import build_questions, format_summary, run_interview, summarize
from llm import ask, provider
from parser import parse_resume
from scorer import final_score, meaning_score


def main(resume_pdf, jd_path, use_ai=True, n=7, preview=False):
    resume = parse_resume(resume_pdf)
    with open(jd_path, encoding="utf-8", errors="ignore") as f:
        jd_text = f.read()

    skills = match_skills(extract_skills(resume["clean_text"], expand=True), jd_text)
    final = final_score(skills["score"], meaning_score(resume["clean_text"], jd_text)["score"])
    print("=" * 62)
    print(f"MATCH SCORE: {final['score']}%   [{final['band'].upper()}]")
    print("=" * 62)

    ai = ask if (use_ai and provider()) else None
    if use_ai and not ai:
        print("No API key found, so answers will get a keyword-based ESTIMATE, not an AI score.")

    plan = build_questions(resume, jd_text, n=n, ask_fn=ai)
    for note in plan["notes"]:
        print("Note:", note)

    if preview:
        for q in plan["questions"]:
            print(f"\n{q['id']}. [{q['type']} | {q['topic']} | {q['source']}] {q['question']}")
        return

    if final["band"] == "low":
        print("\nYour match for this job is low. A real interviewer would probably not reach this stage.")
        print("Run day4.py first to fix the gaps. You can still practise now.")
        try:
            if input("Practise anyway? (y/n): ").strip().lower() != "y":
                return
        except EOFError:
            return
    elif final["band"] == "medium":
        print("\nMedium match: you may get an interview. Practising is a good idea.")

    results = run_interview(plan["questions"], resume, ask_fn=ai)
    print("\n" + format_summary(summarize(results)))


if __name__ == "__main__":
    args = sys.argv[1:]
    use_ai = "--no-ai" not in args
    preview = "--preview" in args
    n = 7
    if "--questions" in args:
        n = int(args[args.index("--questions") + 1])
        del args[args.index("--questions"):args.index("--questions") + 2]
    args = [a for a in args if a not in ("--no-ai", "--preview")]
    if len(args) != 2:
        sys.exit(__doc__)
    main(args[0], args[1], use_ai, n, preview)
