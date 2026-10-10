# Hirequill: AI Resume-JD Matcher and Interview Coach

Upload a resume and a job description. The app scores the match, then either starts a
mock interview (good match) or shows a gap report with what to add and learn (low match).

## Progress
- [x] Day 1: Read resume PDF, clean text, split into sections
- [x] Day 2: Skill extraction (246 skills, resume vs JD comparison)
- [x] Day 3: Match score (skills + meaning, 3 bands, 'any one of' handling)
- [ ] Day 4: Gap report (LLM)
- [ ] Day 5: Interview module
- [ ] Day 6: Streamlit UI
- [ ] Day 7: Testing and deployment

## Setup
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

## Run Day 1
```bash
python make_sample_resume.py          # optional: makes a dummy resume
python parser.py sample_resume.pdf    # or your own resume PDF
```

## Run Day 2
```bash
python day2.py sample_resume.pdf sample_jd.txt   # or your resume + a JD saved as a .txt file
```
Shows the skill match score, matched skills (and which resume section shows them),
missing skills, and soft skills. To add a skill, edit `skills.py`.

## Run Day 3
```bash
python day3.py sample_resume.pdf sample_jd.txt   # or your resume + a JD saved as .txt
```
Final score = 60% skills match + 40% meaning match.

| Final score | Band | What the app does |
|---|---|---|
| 70% and above | High | Start the mock interview |
| 40% to 70% | Medium | Gap report, interview optional |
| Below 40% | Low | Gap report and learning plan |

The meaning score uses a free local AI model (`all-MiniLM-L6-v2`, about 90 MB, downloaded on first run).
If it is not installed, the app falls back to a lighter word-based method and says so.
