# Hirequill: AI Resume-JD Matcher and Interview Coach

Upload a resume and a job description. The app scores the match, then either starts a
mock interview (good match) or shows a gap report with what to add and learn (low match).

## Progress
- [x] Day 1: Read resume PDF, clean text, split into sections
- [x] Day 2: Skill extraction (246 skills, resume vs JD comparison)
- [ ] Day 3: Match score
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
