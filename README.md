# Hirequill: AI Resume-JD Matcher and Interview Coach

Upload a resume and a job description. The app scores the match, then either starts a
mock interview (good match) or shows a gap report with what to add and learn (low match).

## Progress
- [x] Day 1: Read resume PDF, clean text, split into sections
- [x] Day 2: Skill extraction (246 skills, resume vs JD comparison)
- [x] Day 3: Match score (skills + meaning, 3 bands, 'any one of' handling)
- [x] Day 4: Gap report (rule-based + AI suggestions, learning plan)
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

## Run Day 4
```bash
python day4.py sample_resume.pdf sample_jd.txt --no-ai     # works with no API key
python day4.py sample_resume.pdf sample_jd.txt             # adds AI suggestions if a key is set
python day4.py your_resume.pdf jd.txt --hours 15           # study hours per week for the plan
```

### Turn on AI suggestions (free)
1. Get a free key from Google AI Studio (aistudio.google.com) or Groq (console.groq.com).
2. Set it in the terminal you run the app from (never inside a file you upload):
   - Windows (cmd): `set GEMINI_API_KEY=your_key`  (or `set GROQ_API_KEY=your_key`)
   - Mac/Linux: `export GEMINI_API_KEY=your_key`

### How it stays honest
- The AI never quotes your resume. The code picks your weakest real project lines and sends them numbered;
  the AI only rewrites "line 1, line 2...". So every "Before" line is genuinely yours.
- Anything the AI adds that your resume does not back up is flagged `CHECK ... Use only if true`:
  a new skill, a new number, or a claim of level such as "fluent" or "experienced".
- For each line it asks you one question ("how many rows?") so you add the real detail yourself.
- Your name, email, phone and profile links are removed before text is sent to the AI.
- If there is no key, no internet or the free service is busy, the rule-based report still works.
