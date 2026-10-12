# Hirequill: AI Resume-JD Matcher and Interview Coach

Upload a resume and a job description. The app scores the match, then either starts a
mock interview (good match) or shows a gap report with what to add and learn (low match).

## Progress
- [x] Day 1: Read resume PDF, clean text, split into sections
- [x] Day 2: Skill extraction (246 skills, resume vs JD comparison)
- [x] Day 3: Match score (skills + meaning, 3 bands, 'any one of' handling)
- [x] Day 4: Gap report (rule-based + AI suggestions, learning plan)
- [x] Day 5: Mock interview (questions from your resume + job, scoring, summary)
- [x] Day 6: Streamlit web app (upload, score, gap report, interview, re-score)
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

## Run Day 5: mock interview
```bash
python day5.py sample_resume.pdf sample_jd.txt --preview --no-ai   # only list the questions
python day5.py your_resume.pdf jd.txt --no-ai                      # interview, keyword-estimate scoring
python day5.py your_resume.pdf jd.txt                              # interview, AI scoring if a key is set
python day5.py your_resume.pdf jd.txt --questions 5                # 3 to 12 questions
python test_interview.py                                           # self-test, should end with ALL TESTS PASSED
```
In the interview: type your answer, then press Enter on an empty line to submit. Type `skip` to skip a question
or `quit` to stop (Ctrl+C also works). If an answer scores below 6/10 you can retry that question once.

### What it asks (about 7 questions)
1. Tell me about yourself.
2. A walk-through question for each of your real projects (found in your resume, up to 3).
3. Technical questions on skills you list AND the job wants (SQL, Python, Excel, Tableau and more).
4. One question on a skill the job wants that is missing from your resume (how would you learn it?).
5. A behavioural question (teamwork, solving a problem).

### How answers are scored
- **With an AI key:** the AI judges your answer against the key points of a good answer. It is told to
  ignore any instructions hidden inside your answer, and the score is kept between 0 and 10.
- **Without a key:** a keyword check gives an ESTIMATE and says so. It cannot understand meaning, so a
  longer answer is needed to earn credit for each point, and a list of keywords does not score well.
- Very short answers are capped at 3/10 either way.
- Your answers pass through the same redaction as Day 4 (email, phone and profile links removed) before
  they are sent to the AI.

### The summary
Average score, strong answers, topics to practise first, the key points you missed most often, and a verdict.

### Add your own interview questions
Questions and what a good answer covers live in `questionbank.py`. Add a skill and a few key points
and the interview will use it.

## Day 6: the web app

```
pip install -r requirements.txt
streamlit run app.py
```

Open the link it prints (usually http://localhost:8501).

**How to use it**
1. Upload your resume PDF and paste a job description, then press **Analyze**. Or press **Try a sample**.
2. Read the score: 60% skills + 40% meaning. High (70+) opens the **Mock interview**; medium and low open the **Gap report**.
3. **Match details** shows matched/missing skills and where each skill appears in your resume.
4. **Gap report** shows weak points, missing skills and a free learning plan. The hours/week slider changes the plan.
   Press **Get AI suggestions** for rewrites of your real lines (needs an API key).
5. **Mock interview**: answer in the chat box. A weak answer can be retried once. Skip or end any time, then read the summary.
6. **Re-score**: improve your resume, upload the new PDF, and see the score change for the same job.

**Safety and limits**
- The resume is read in memory only, never saved. Limits: 5 MB, 6 pages, 12,000 characters of job description.
- Each visit gets a cap of AI requests (`HIREQUILL_AI_LIMIT`, default 40) so a public demo cannot use up the free quota.
  After that, the rule-based report and estimated scores keep working.
- If the AI is busy, the page shows a friendly message and everything else still works.
- Set `HIREQUILL_BACKEND=tfidf` on small free hosts to skip the large language model download.

**Code layout**: `pipeline.py` (input checks, scoring, AI cap) and `session.py` (interview flow) hold the logic and have no
Streamlit in them, so `python test_app_logic.py` tests them without a browser. `app.py` only draws the page.
