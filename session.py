"""Day 6: the mock interview as a small state machine.

The web page (app.py) only draws what this object holds and calls its methods, so the whole flow
can be tested without a browser. It follows the same rules as the terminal version in interview.py:
an answer below 6/10 can be retried once, questions can be skipped, and you can end early.
"""
import interview as iv

PASS_MARK = 6          # below this, offer one retry
MAX_ANSWER_CHARS = 3000


def question_message(q: dict, total: int) -> str:
    return f"**Question {q['id']} of {total}** · {q['type']}\n\n{q['question']}"


def feedback_message(r: dict) -> str:
    label = "AI score" if r.get("method") == "ai" else "Estimated score"
    parts = [f"**{label}: {r['score']}/10**"]
    if r.get("feedback"):
        parts.append(r["feedback"])
    bullets = [f"- Covered: {p}" for p in r.get("covered", [])[:3]] + \
              [f"- Missing: {p}" for p in r.get("missed", [])[:3]]
    if bullets:
        parts.append("\n".join(bullets))
    if r.get("tip"):
        parts.append(f"**Tip:** {r['tip']}")
    return "\n\n".join(parts)


class InterviewSession:
    def __init__(self, resume: dict, jd_text: str, n: int = 7, ask_fn=None, questions=None):
        self.resume = resume
        self.ask_fn = ask_fn
        if questions is not None:             # e.g. "practise weak topics again"
            self.questions = [{**q, "id": i} for i, q in enumerate(questions, 1)]
            self.ai_used, self.notes = False, []
        else:
            plan = iv.build_questions(resume, jd_text, n=n, ask_fn=ask_fn)
            self.questions = plan["questions"]
            self.ai_used = plan["ai_used"]
            self.notes = plan["notes"]
        self.index = 0
        self.results = []
        self.log = []                 # [(role, text)] shown as chat bubbles
        self.pending = None           # a low-scoring answer waiting for "retry" or "continue"
        self.retried = False
        self.done = False
        self._announce()

    # ------------------------------------------------------------ reading state
    @property
    def total(self) -> int:
        return len(self.questions)

    @property
    def current(self):
        return self.questions[self.index] if not self.done and self.index < self.total else None

    @property
    def awaiting_answer(self) -> bool:
        return self.current is not None and self.pending is None

    # ------------------------------------------------------------ moving through the interview
    def _announce(self):
        if self.index < self.total:
            self.log.append(("assistant", question_message(self.questions[self.index], self.total)))
        else:
            self._finish("That was the last question. Here is how it went.")

    def _finish(self, message: str):
        self.done = True
        self.pending = None
        self.log.append(("assistant", message))

    def _record(self, result: dict):
        self.results.append(result)
        self.retried = False
        self.pending = None
        self.index += 1
        self._announce()

    def submit(self, answer: str) -> bool:
        """Score an answer. Returns False if there was nothing to score."""
        answer = (answer or "").strip()[:MAX_ANSWER_CHARS]
        if not answer or not self.awaiting_answer:
            return False
        q = self.current
        self.log.append(("user", answer))
        r = iv.score_answer(q, answer, self.resume, self.ask_fn)
        self.log.append(("assistant", feedback_message(r)))
        result = {"question": q, "answer": answer, "skipped": False, **r}
        if r["score"] < PASS_MARK and not self.retried:
            self.pending = result
            self.log.append(("assistant", "That answer was a little thin. You can retry this question once, "
                                          "or continue to the next one."))
        else:
            self._record(result)
        return True

    def retry(self):
        if self.pending is None:
            return
        self.pending = None
        self.retried = True
        self.log.append(("assistant", "Take another go:\n\n" + self.current["question"]))

    def accept(self):
        """Keep the low score and move on."""
        if self.pending is not None:
            self._record(self.pending)

    def skip(self):
        if not self.awaiting_answer:
            return
        q = self.current
        self.log.append(("assistant", "Skipped."))
        self._record({"question": q, "answer": "", "skipped": True, "score": 0.0, "missed": [], "method": "none"})

    def end(self):
        if not self.done:
            self._finish("Interview ended. Here is how it went so far.")

    # ------------------------------------------------------------ results
    def summary(self) -> dict:
        return iv.summarize(self.results)

    def transcript(self) -> str:
        lines = ["HIREQUILL MOCK INTERVIEW", "=" * 40, ""]
        for r in self.results:
            q = r["question"]
            lines.append(f"Q{q['id']} [{q['type']}] {q['question']}")
            if r.get("skipped"):
                lines += ["   (skipped)", ""]
                continue
            label = "AI score" if r.get("method") == "ai" else "Estimated score"
            lines += [f"   Your answer: {r['answer']}", f"   {label}: {r['score']}/10"]
            if r.get("feedback"):
                lines.append(f"   Feedback: {r['feedback']}")
            if r.get("tip"):
                lines.append(f"   Tip: {r['tip']}")
            lines.append("")
        lines.append(iv.format_summary(self.summary()))
        return "\n".join(lines)
