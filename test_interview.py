"""Self-test for the mock interview (no PDF, no API key, no internet needed).

Run:  python test_interview.py
Every line should say ok. If one says FAIL, the interview logic broke.
"""
import json

import interview as iv
import questionbank as qb
from llm import LLMUnavailable
from parser import clean_text, split_sections

RESUME_TEXT = """ASHA RAO
SKILLS
Python, SQL, Tableau, Django, OpenCV
PROJECTS
Brain Tumor Detection
Tech Stack: Django, OpenCV, TensorFlow
- Built a Django backend serving a trained model with OpenCV preprocessing and a web UI.
Hematovision
Technologies: Flask, MobileNetV2
- Deployed a MobileNetV2 classifier behind a Flask API that returns JSON.
EDUCATION
B.Tech 2022-2026"""
JD = ("Data Analyst. Write SQL queries, use Python and Excel, build dashboards in Tableau or Power BI. "
      "Knowledge of data warehousing and machine learning is a plus.")

_t = clean_text(RESUME_TEXT)
RESUME = {"clean_text": _t, "sections": split_sections(_t)}
SQL_Q = {"type": "technical", "topic": "sql", "context": "",
         "question": qb.BANK["sql"][0]["question"], "points": qb.BANK["sql"][0]["points"]}
failures = 0


def check(name, condition):
    global failures
    failures += not condition
    print(("ok   " if condition else "FAIL ") + name)


# --- projects
blocks = {b["title"]: b["context"] for b in iv.project_blocks(RESUME)}
check("finds both projects, including a one-word title", set(blocks) == {"Brain Tumor Detection", "Hematovision"})
check("'Tech Stack: ...' is not mistaken for a project", not any("Stack" in t for t in blocks))
check("each project keeps only its own lines", "Flask" not in blocks["Brain Tumor Detection"]
      and "Django" not in blocks["Hematovision"])

# --- choosing questions
plan = iv.build_questions(RESUME, JD, n=7)
qs = plan["questions"]
check("builds 7 questions, intro first", len(qs) == 7 and qs[0]["type"] == "intro")
check("asks a SQL question for a data analyst job", any(q["topic"] == "sql" for q in qs))
check("no question is repeated", len({q["question"] for q in qs}) == len(qs))
check("question count is limited to 12", len(iv.build_questions(RESUME, JD, n=99)["questions"]) <= 12)

# --- scoring without AI
good = ("An INNER JOIN returns only the rows that match in both tables, for example customers who have orders. "
        "A LEFT JOIN returns every row from the left table and fills NULL where the right table has no match.")
check("a good answer scores high", iv.score_answer(SQL_Q, good)["score"] >= 9)
check("a list of keywords does NOT score high",
      iv.score_answer(SQL_Q, "inner match both left null every example customer order table")["score"] <= 3.5)
check("a wrong answer scores near zero", iv.score_answer(SQL_Q, "A join puts colours on a chart in a dashboard "
                                                         "and it is mostly used by designers I think")["score"] <= 1)
check("an empty answer scores 0", iv.score_answer(SQL_Q, "  ")["score"] == 0)
check("a very short answer is capped", iv.score_answer(SQL_Q, "inner join matches rows")["score"] <= 3)
check("'one' does not match 'someone'", not iv._has_keyword(" someone said so ", "one"))
check("stems still match ('aggregat' in 'aggregation')", iv._has_keyword(" we use aggregation ", "aggregat"))

# --- scoring with a pretend AI
def fake(reply):
    return lambda *a, **k: reply


ai = iv.score_answer(SQL_Q, good, None, fake(json.dumps({"score": 8, "covered": [1, 2], "missed": [3]})))
check("uses the AI score when the reply is valid", ai["method"] == "ai" and ai["score"] == 8.0)
check("clamps an impossible AI score",
      iv.score_answer(SQL_Q, good, None, fake(json.dumps({"score": 99})))["score"] == 10.0)
check("falls back to the estimate on a bad AI reply", iv.score_answer(SQL_Q, good, None, fake("sorry"))["method"] == "estimate")


def down(*a, **k):
    raise LLMUnavailable("busy")


check("falls back to the estimate when the AI is down", iv.score_answer(SQL_Q, good, None, down)["method"] == "estimate")
sent = {}


def spy(prompt, system, want_json=False):
    sent["p"] = prompt
    return json.dumps({"score": 1})


iv.score_answer(SQL_Q, "call me on 9876543210 or mail a@b.com. " + good, None, spy)
check("phone and email are removed before sending to the AI", "9876543210" not in sent["p"] and "a@b.com" not in sent["p"])
check("the answer is sent as data, not instructions", "<<<ANSWER" in sent["p"])

# --- AI question wording is guarded
pid = next(q["id"] for q in qs if q["type"] == "project")


def reword(text):
    reply = json.dumps({"questions": [{"id": pid, "question": text}]})
    return iv.build_questions(RESUME, JD, n=7, ask_fn=fake(reply))["ai_used"]


check("accepts a faithful rewording", reword("In Brain Tumor Detection, how did you use OpenCV before the model?"))
check("rejects an invented skill", not reword("In Brain Tumor Detection, how did you deploy it on Kubernetes?"))
check("rejects another project's skill", not reword("In Brain Tumor Detection, how did you build the Flask API?"))
check("rejects an invented number", not reword("In Brain Tumor Detection, how did you handle 5000 images?"))

# --- running the interview


def scripted(lines):
    it = iter(lines)

    def read(prompt=""):
        try:
            return next(it)
        except StopIteration:
            raise EOFError
    return read


quiet = lambda *_: None
check("closed input ends the interview without a crash", iv.run_interview(qs[:2], RESUME, scripted([]), quiet) == [])


def interrupt(prompt=""):
    raise KeyboardInterrupt


check("Ctrl+C ends the interview without a crash", iv.run_interview(qs[:2], RESUME, interrupt, quiet) == [])
done = iv.run_interview(qs[:3], RESUME, scripted(["skip", "skip", "quit"]), quiet)
check("skip records a skipped question", len(done) == 2 and all(r["skipped"] for r in done))

# --- summary
summary = iv.summarize([
    {"question": {"type": "technical", "topic": "sql"}, "score": 9.0, "missed": [], "method": "ai", "skipped": False},
    {"question": {"type": "project", "topic": "Hematovision"}, "score": 3.0, "missed": ["the result"], "method": "ai", "skipped": False},
])
check("summary finds the strong and the weak topics",
      summary["average"] == 6.0 and "sql" in summary["strong_topics"][0] and "Hematovision" in summary["weak_topics"][0])
check("summary copes with nothing answered", iv.summarize([])["answered"] == 0)

print(f"\n{'ALL TESTS PASSED' if not failures else str(failures) + ' TEST(S) FAILED'}")
raise SystemExit(1 if failures else 0)
