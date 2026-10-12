"""Day 7: check that the score matches your own judgement, using real resume/job pairs.

1. Put your pairs in a file called pairs.csv (one row per pair):
       name,resume,jd,expected
       Deloitte analyst,my_resume.pdf,deloitte_analyst.txt,medium
       Java backend job,my_resume.pdf,java_backend.txt,low
   'expected' is YOUR honest opinion: high (you would apply and expect a call), medium, or low (clearly not your field).
   Use 10 or more pairs. Include some clear matches and some clear mismatches, and a few friends' resumes if you can.
2. Run:  python calibrate.py pairs.csv
3. Look at the table. Rows marked <-- are where the app disagrees with you. Send me the output.
"""
import csv
import os
import sys

import pipeline as pl
from parser import parse_resume
from scorer import BANDS, CALIBRATION

BAND_ORDER = {"low": 0, "medium": 1, "high": 2}


def main(path):
    base = os.path.dirname(os.path.abspath(path))
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    results = []
    for row in rows:
        resume_path = os.path.join(base, row["resume"].strip())
        jd_path = os.path.join(base, row["jd"].strip())
        try:
            resume = parse_resume(resume_path)
            jd = open(jd_path, encoding="utf-8", errors="ignore").read()
        except Exception as error:
            print(f"SKIPPED {row.get('name')}: {error}")
            continue
        emb = pl.analyze(resume, jd, backend="embedding")      # exactly what the web app computes
        tf = pl.analyze(resume, jd, backend="tfidf")
        results.append({"name": row["name"], "expected": row["expected"].strip().lower(),
                        "skills": emb["skills"]["score"], "emb": emb["meaning"]["score"],
                        "emb_raw": emb["meaning"]["raw"], "emb_backend": emb["meaning"]["backend"],
                        "tfidf": tf["meaning"]["score"], "tfidf_final": tf["final"]["score"],
                        "tfidf_band": tf["final"]["band"], "final": emb["final"]["score"],
                        "band": emb["final"]["band"], "skill_count": emb["skills"]["jd_skill_count"]})

    print(f"\n{'name':28} {'#skl':>4} {'skills':>7} {'meaning':>8} {'final':>6}  {'app says':9} {'you said':9} | {'lite final':>10} {'lite says':9}")
    print("-" * 104)
    agree = 0
    for r in results:
        gap = BAND_ORDER[r["band"]] - BAND_ORDER.get(r["expected"], BAND_ORDER[r["band"]])
        mark = "" if gap == 0 else ("  <-- too high" if gap > 0 else "  <-- too low")
        agree += gap == 0
        print(f"{r['name'][:28]:28} {r['skill_count']:>4} {r['skills']:>7} {r['emb']:>8} {r['final']:>6}  {r['band']:9} {r['expected']:9} | "
              f"{r['tfidf_final']:>10} {r['tfidf_band']:9}{mark}")
    if not results:
        return
    print(f"\nAgreement (full model): {agree} of {len(results)} pairs in the same band as your judgement.")
    lite = sum(r["tfidf_band"] == r["expected"] for r in results)
    print(f"Agreement (lite word-based version used on the free host): {lite} of {len(results)}.")
    if any(r["emb_backend"] != "embedding" for r in results):
        print("WARNING: the AI meaning model did not load for some rows, so 'meaning' used the word-based method.")

    print("\nMeaning raw similarity by what you expected (used to set CALIBRATION):")
    for level in ("low", "medium", "high"):
        raws = [r["emb_raw"] for r in results if r["expected"] == level]
        if raws:
            print(f"  {level:7} n={len(raws):2}  min {min(raws):.3f}  average {sum(raws) / len(raws):.3f}  max {max(raws):.3f}")
    print(f"\nCurrent CALIBRATION (raw -> 0..100): {CALIBRATION}")
    print(f"Bands: {BANDS}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
