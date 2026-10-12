"""Self-test for the Day 6 logic (pipeline.py + session.py). No browser, no API key, no internet.

Run:  python test_app_logic.py        Every line should say ok.
"""
import io

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

import pipeline as pl
import samples
from llm import LLMUnavailable
from session import InterviewSession, feedback_message

failures = 0


def check(name, condition):
    global failures
    failures += not condition
    print(("ok   " if condition else "FAIL ") + name)


def make_pdf(text: str, pages: int = 1) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    lines = text.split("\n")
    for _ in range(pages):
        y = 800
        for line in lines:
            c.drawString(40, y, line[:110])
            y -= 14
        c.showPage()
    c.save()
    return buf.getvalue()


def problem(fn, *a):
    try:
        fn(*a)
    except pl.InputProblem as e:
        return str(e)
    return None


# --- getting a resume in
check("empty upload is refused", problem(pl.resume_from_pdf, b"") is not None)
check("a non-PDF is refused", "PDF" in (problem(pl.resume_from_pdf, b"hello world") or ""))
check("a huge file is refused", problem(pl.resume_from_pdf, b"%PDF" + b"0" * (6 * 1024 * 1024)) is not None)
check("a broken PDF is refused", problem(pl.resume_from_pdf, b"%PDF-1.4 not really a pdf") is not None)
check("too many pages is refused", "pages" in (problem(pl.resume_from_pdf, make_pdf("SKILLS\nPython", pages=8)) or ""))
blank = make_pdf("")
check("a blank/scanned PDF gives a friendly message", problem(pl.resume_from_pdf, blank) is not None)
resume = pl.resume_from_pdf(make_pdf(samples.RESUME))
check("a real text PDF is read in memory", "Tableau" in resume["clean_text"] and "skills" in resume["sections"])

# --- scoring
check("empty job description is refused", problem(pl.analyze, resume, "   ") is not None)
a = pl.analyze(resume, samples.JOB, backend="tfidf")
check("analysis has every field the page needs",
      all(k in a for k in ("jd", "jd_key", "skills", "meaning", "final", "where", "warnings")))
check("score is 0-100 and has a band", 0 <= a["final"]["score"] <= 100 and a["final"]["band"] in ("high", "medium", "low"))
check("final = 60% skills + 40% meaning",
      abs(a["final"]["score"] - (0.6 * a["skills"]["score"] + 0.4 * a["meaning"]["score"])) < 0.2)
check("a very short job description gets a warning", pl.analyze(resume, "Python developer", backend="tfidf")["warnings"])
check("job description is capped", len(pl.clean_jd("word " * 20000)) <= pl.MAX_JD_CHARS)


# --- job-site labels and thin job descriptions
listing = "Write SQL queries and build dashboards in Tableau using Python and Excel every day.\nRole: Analyst\nDepartment: Engineering - Software & QA\nUG: Any Graduate"
check("listing labels are removed from a job description", "Department" not in pl.clean_jd(listing) and "SQL" in pl.clean_jd(listing))
check("labels alone do not empty the job description", pl.clean_jd("Role: Analyst\nDepartment: Data") != "")
thin = pl.analyze(resume, "Support engineer. Must know SQL. Provide helpdesk support to users over phone and email, "
                  "reset passwords, and document every ticket carefully for the team lead.", backend="tfidf")
check("one recognised skill does not give a high score", thin["skills"]["jd_skill_count"] <= 1 and thin["final"]["band"] != "high")

# --- history / re-score
h1 = pl.history_entry("First", a)
better = pl.resume_from_text(samples.RESUME + "\nCompleted a Power BI course and used ETL and data warehousing in a project.")
a2 = pl.analyze(better, samples.JOB, backend="tfidf")
h2 = pl.history_entry("Second", a2)
check("score change is shown for the same job", pl.score_change([h1, h2]) == round(h2["final"] - h1["final"], 1))
check("score change is a gain after adding real skills", pl.score_change([h1, h2]) > 0)
other = pl.analyze(resume, "Backend engineer. Build REST APIs in Java and Spring Boot with MySQL and Docker on AWS, "
                   "write unit tests, and work with Kubernetes and CI pipelines every day.", backend="tfidf")
check("no score change across different jobs", pl.score_change([h1, pl.history_entry("x", other)]) is None)
check("no score change on the first try", pl.score_change([h1]) is None)
check("high match goes to the interview", pl.default_view("high") == "Mock interview")
check("low and medium go to the gap report", pl.default_view("low") == pl.default_view("medium") == "Gap report")

# --- AI budget
calls = []
budget = pl.AiBudget(limit=2, cooldown=0)
guarded = budget.wrap(lambda *a, **k: calls.append(1) or "reply")
guarded(); guarded()
try:
    guarded()
    blocked = False
except LLMUnavailable:
    blocked = True
check("AI budget blocks calls past the limit", blocked and len(calls) == 2 and budget.remaining == 0)

# --- cooldown and daily guard
clock = [100.0]
b2 = pl.AiBudget(limit=10, cooldown=3, clock=lambda: clock[0])
g2 = b2.wrap(lambda *a, **k: "ok")
g2()
try:
    g2(); cooled = False
except LLMUnavailable as e:
    cooled = "wait" in str(e)
clock[0] += 4
check("cooldown refuses a too-quick second call, then allows it", cooled and g2() == "ok" and b2.used == 2)
day = ["d1"]
guard = pl.DailyGuard(limit=2, today=lambda: day[0])
check("daily guard allows up to its limit", guard.take() and guard.take() and not guard.take())
day[0] = "d2"
check("daily guard resets on a new day", guard.take())
sb = pl.AiBudget(limit=10, cooldown=0, shared=pl.DailyGuard(limit=0))
try:
    sb.wrap(lambda *a, **k: "ok")(); full = False
except LLMUnavailable as e:
    full = "busy" in str(e) and sb.used == 0
check("a used-up site quota gives a friendly message and costs the visitor nothing", full)

# --- interview session
RES = pl.resume_from_text(samples.RESUME)
s = InterviewSession(RES, samples.JOB, n=4)
check("session starts with the first question shown", s.total == 4 and s.awaiting_answer and s.log[0][0] == "assistant")
check("empty answer is ignored", s.submit("   ") is False and not s.results)
s.submit("I am a B.Tech graduate who built a Tableau dashboard and analysed rainfall data with Python and SQL.")
check("an answer is scored and logged", s.log[-2][0] == "user" or s.results or s.pending)
# a bad answer to the next question: retry once, then it is recorded
while s.pending is None and not s.done:
    s.submit("I do not know")
check("a weak answer offers a retry", s.pending is not None)
before = len(s.results)
s.retry()
check("retry asks the same question again", s.pending is None and s.retried and len(s.results) == before)
s.submit("not sure")
check("after one retry the answer is kept and we move on", s.pending is None and len(s.results) == before + 1)
s.skip()
check("skip records a skipped question", s.results[-1]["skipped"] is True)
s.end()
check("end finishes the interview", s.done and s.current is None and not s.awaiting_answer)
check("submit after the end does nothing", s.submit("hello there") is False)
check("summary and transcript work", s.summary()["answered"] >= 1 and "HIREQUILL MOCK INTERVIEW" in s.transcript())

s2 = InterviewSession(RES, samples.JOB, n=3)
s2.submit("x" * 9000)
check("an overlong answer is trimmed", len(s2.results[-1]["answer"] if s2.results else s2.pending["answer"]) <= 3000)
s3 = InterviewSession(RES, samples.JOB, n=3)
for _ in range(3):
    s3.skip()
check("finishing all questions ends the interview", s3.done and len(s3.results) == 3)
check("a summary with nothing answered does not crash", s3.summary()["answered"] == 0 and "HIREQUILL" in s3.transcript())
redo = InterviewSession(RES, samples.JOB, questions=[r["question"] for r in s3.results[:2]])
check("practising chosen questions again renumbers them", [q["id"] for q in redo.questions] == [1, 2] and redo.total == 2)

msg = feedback_message({"score": 4.0, "method": "estimate", "covered": ["join"], "missed": ["null"], "tip": "Add an example."})
check("feedback keeps the tip on its own paragraph", "\n\n**Tip:**" in msg and "- Missing: null\n\n" in msg)

print(f"\n{'ALL TESTS PASSED' if not failures else str(failures) + ' TEST(S) FAILED'}")
raise SystemExit(1 if failures else 0)
