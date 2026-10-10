# ResumeIQ: AI Resume-JD Matcher and Interview Coach

Upload a resume and a job description. The app scores the match, then either starts a
mock interview (good match) or shows a gap report with what to add and learn (low match).

## Progress
- [x] Day 1: Read resume PDF, clean text, split into sections
- [ ] Day 2: Skill extraction
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
