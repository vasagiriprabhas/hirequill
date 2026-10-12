"""Hirequill web app (Day 6).   Run:  streamlit run app.py

Flow: upload resume PDF + paste job description -> match score -> gap report and/or mock interview,
and a re-score box to see the score change after you improve the resume.
All real work lives in pipeline.py, session.py, gap_report.py and interview.py (tested without a browser).
This file only draws the page.
"""
import streamlit as st

import gap_report as gr
import pipeline as pl
import samples
from llm import ask as raw_ask, provider
from session import MAX_ANSWER_CHARS, InterviewSession

st.set_page_config(page_title="Hirequill", page_icon="🪶", layout="centered")

VIEWS = ["Match details", "Gap report", "Mock interview"]
BAND_TEXT = {
    "high": ("success", "Strong match. Practise the interview for this job."),
    "medium": ("warning", "Decent match. Fix the gaps below, and the interview is optional practice."),
    "low": ("error", "Weak match for now. Start with the gap report: what to fix and what to learn."),
}

# ------------------------------------------------------------------ state
@st.cache_resource
def daily_guard():
    """One counter shared by every visitor of this server."""
    return pl.DailyGuard()


S = st.session_state
S.setdefault("budget", pl.AiBudget(shared=daily_guard()))
S.setdefault("history", [])
S.setdefault("analysis", None)
S.setdefault("resume", None)
S.setdefault("report", None)
S.setdefault("ai_result", None)
S.setdefault("interview", None)
S.setdefault("hours", 10)
S.setdefault("view", VIEWS[0])


def ai_function(enabled: bool):
    """The AI function the rest of the app uses, or None (rule-based only)."""
    if enabled and provider():
        return S.budget.wrap(raw_ask)
    return None


def run_analysis(resume: dict, jd_text: str, label: str, reset: bool):
    """Score, store the result, and keep the history. reset=True means a brand new resume/job pair."""
    analysis = pl.analyze(resume, jd_text)
    if reset:
        S.history = []
    S.history.append(pl.history_entry(label, analysis))
    S.resume, S.analysis = resume, analysis
    S.report = gr.build_report(resume, analysis["jd"], use_ai=False, hours_per_week=S.hours)
    S.ai_result = None
    S.interview = None
    if reset:
        S.view = pl.default_view(analysis["final"]["band"])


# ------------------------------------------------------------------ header + sidebar
st.title("🪶 Hirequill")
st.caption("Check how well your resume matches a job, fix the gaps, and practise the interview.")

with st.expander("Privacy: is my resume stored?"):
    st.write("No. Your resume is read in memory and is not saved to disk or a database. It disappears when you "
             "close or refresh this page. If AI features are on, only the text (with your email, phone number "
             "and profile links removed) is sent to the AI service to write suggestions or score answers.")

with st.sidebar:
    st.header("AI features")
    use_ai = st.checkbox("Use AI", value=True, help="Turn off to use only the rule-based report and estimated scores.")
    if provider():
        st.caption(f"AI is available. {S.budget.remaining} AI requests left this visit.")
    else:
        st.caption("No AI key is set on this server, so the app uses its rule-based mode.")
    st.caption("If the AI is busy you will see a message; wait a minute and try again. Everything else keeps working.")
    if S.analysis and st.button("Start over"):
        for key in ("analysis", "resume", "report", "ai_result", "interview"):
            S[key] = None
        S.history = []
        S.view = VIEWS[0]
        st.rerun()

ask_fn = ai_function(use_ai)

# ------------------------------------------------------------------ input form
with st.form("inputs"):
    pdf = st.file_uploader("1. Your resume (PDF)", type=["pdf"])
    jd_text = st.text_area("2. The job description", height=200, max_chars=pl.MAX_JD_CHARS,
                           placeholder="Paste the full job description here, including skills and responsibilities.")
    c1, c2 = st.columns(2)
    go = c1.form_submit_button("Analyze", type="primary")
    demo = c2.form_submit_button("Try a sample")

if go or demo:
    try:
        with st.spinner("Reading and scoring..."):
            if demo:
                run_analysis(pl.resume_from_text(samples.RESUME), samples.JOB, "Sample resume", reset=True)
            else:
                if pdf is None:
                    raise pl.InputProblem("Upload your resume as a PDF first.")
                run_analysis(pl.resume_from_pdf(pdf.getvalue()), jd_text, "First try", reset=True)
    except pl.InputProblem as problem:
        st.error(str(problem))
    except Exception:
        st.error("Something went wrong while scoring. Please try again, or try a different PDF.")

analysis = S.analysis
if analysis is None:
    st.info("Upload a resume and paste a job description, or press **Try a sample**.")
    st.stop()

# ------------------------------------------------------------------ score card
final, skills, meaning = analysis["final"], analysis["skills"], analysis["meaning"]
st.divider()
m1, m2, m3 = st.columns(3)
change = pl.score_change(S.history)
m1.metric("Match score", f"{final['score']}%", delta=None if change is None else f"{change:+}")
m2.metric("Skills (60%)", f"{skills['score']}%")
m3.metric("Meaning (40%)", f"{meaning['score']}%")
st.progress(min(max(final["score"] / 100, 0.0), 1.0))
kind, text = BAND_TEXT[final["band"]]
getattr(st, kind)(text)
method = "AI language model" if meaning.get("backend") == "embedding" else "word-overlap method"
st.caption(f"Meaning score uses the {method}. Scores are a guide, not a promise: real employers use their own filters.")
if meaning.get("note"):
    st.caption(meaning["note"])
for warning in analysis["warnings"]:
    st.warning(warning)

view = st.radio("View", VIEWS, key="view", horizontal=True, label_visibility="collapsed")


# ------------------------------------------------------------------ view 1: match details
def show_details():
    left, right = st.columns(2)
    with left:
        st.subheader("Matched")
        for item in skills["matched"] or ["Nothing matched yet."]:
            st.write("✅ " + item if skills["matched"] else item)
    with right:
        st.subheader("Missing")
        for item in skills["missing"] or ["Nothing missing."]:
            st.write("❌ " + item if skills["missing"] else item)
    if analysis["where"]:
        st.subheader("Where your skills appear")
        st.caption("A skill listed only under Skills is weaker than one shown in a project.")
        rows = ["| Skill | Skills list | Projects | Other |", "|---|---|---|---|"]
        for skill in skills["matched_skills"]:
            w = set(analysis["where"].get(skill, []))
            cells = ["skills" in w, "projects" in w, bool(w - {"skills", "projects"})]
            rows.append(f"| {skill} | " + " | ".join("✓" if c else "" for c in cells) + " |")
        st.markdown("\n".join(rows))
    if skills["soft_in_jd"]:
        st.subheader("Soft skills the job mentions")
        st.write(", ".join(skills["soft_in_jd"]) + ".  Show these with examples, not just the words.")
    if skills["extra"]:
        st.subheader("Extra skills you have")
        st.write(", ".join(skills["extra"]))


# ------------------------------------------------------------------ view 2: gap report
def report_text() -> str:
    report = dict(S.report)
    report["ai"] = S.ai_result
    return gr.format_report(report)


def show_gap_report():
    report = S.report
    st.subheader("Weak points in your resume")
    if not report["weak_points"]:
        st.success("No structural problems found.")
    icon = {"high": "🔴", "medium": "🟠", "low": "🟡"}
    for w in report["weak_points"]:
        with st.container(border=True):
            st.markdown(f"{icon.get(w['severity'], '')} **{w['issue']}**")
            st.write(w["why"])
            st.markdown(f"**Fix:** {w['fix']}")

    st.subheader("Skills the job wants that your resume does not show")
    if report["missing"]:
        for m in report["missing"]:
            st.write(f"- {m['label']}  (job mentions it {m['mentions']}x)")
    else:
        st.success("You cover every skill this job lists.")
    if report["soft_missing"]:
        st.caption("Soft skills to show with examples: " + ", ".join(report["soft_missing"]))

    st.subheader("Free learning plan")
    hours = st.slider("Hours per week you can study", 2, 40, key="hours")
    plan = gr.learning_plan(report["missing"], hours)
    if not plan["steps"]:
        st.write("Nothing to learn for this job.")
    for i, step in enumerate(plan["steps"], 1):
        with st.expander(f"{i}. {step['label']}  (about {step['hours']} hours)"):
            for r in step["resources"]:
                st.write("- " + r)
            st.markdown(f"**Then:** {step['prove_it']}")
    if plan["steps"]:
        st.info(f"Total about {plan['total_hours']} hours = {plan['weeks']} weeks at {hours} hours/week.")
    if plan["skipped"]:
        st.caption("Later (not in this plan): " + ", ".join(plan["skipped"]))

    st.subheader("AI rewrite suggestions")
    st.caption("The AI rewrites your real lines. Check every suggestion: use it only if it is true.")
    if ask_fn is None:
        st.write("AI is off or not available, so this section is skipped. The report above still works.")
    elif st.button("Get AI suggestions"):
        with st.spinner("Asking the AI..."):
            S.ai_result = gr.ai_suggestions(S.resume, analysis["jd"], skills["matched_skills"], ask_fn)
    ai = S.ai_result
    if ai is not None and not ai["ok"]:
        st.warning(f"AI suggestions are not available right now: {ai['note']}")
    elif ai is not None:
        if ai["summary_rewrite"]:
            s_ = ai["summary_rewrite"]
            with st.container(border=True):
                st.markdown("**Suggested summary**")
                st.write(s_["text"])
                for f in s_["flags"]:
                    st.warning(f"Check: {f}. Use only if true.")
        for b in ai["bullet_rewrites"]:
            with st.container(border=True):
                st.markdown(f"**Before:** {b['original']}")
                st.markdown(f"**After:** {b['improved']}")
                if b["why"]:
                    st.caption("Why: " + b["why"])
                if b["question"]:
                    st.markdown(f"*Add a real detail:* {b['question']}")
                for f in b["flags"]:
                    st.warning(f"Check: {f}. Use only if true.")
        if ai.get("removed_unverified"):
            st.caption(f"Removed {ai['removed_unverified']} suggestion(s): the AI referred to lines that do not exist.")
        st.caption("Replace any [bracketed] placeholder with a real number, or delete it.")

    st.download_button("Download this report (.txt)", report_text(), file_name="hirequill_gap_report.txt")


# ------------------------------------------------------------------ view 3: mock interview
def show_interview():
    session = S.interview
    if session is None:
        if final["band"] == "low":
            st.info("Your match for this job is low, so a real interviewer may not reach this stage. "
                    "You can still practise, but the gap report is the better first step.")
        elif final["band"] == "medium":
            st.caption("Optional for a medium match, but good practice.")
        n = st.slider("Number of questions", 3, 12, 7)
        if st.button("Start interview", type="primary"):
            with st.spinner("Preparing your questions..."):
                S.interview = InterviewSession(S.resume, analysis["jd"], n=n, ask_fn=ask_fn)
            st.rerun()
        if ask_fn is None:
            st.caption("AI is off, so answers get a keyword-based ESTIMATE, not a real AI score.")
        return

    for note in session.notes:
        st.caption(note)
    for role, message in session.log:
        with st.chat_message(role):
            st.markdown(message)

    if session.pending is not None:
        b1, b2 = st.columns(2)
        if b1.button("Retry this question"):
            session.retry()
            st.rerun()
        if b2.button("Continue"):
            session.accept()
            st.rerun()
    elif session.awaiting_answer:
        answer = st.chat_input("Type your answer and press Enter", max_chars=MAX_ANSWER_CHARS)
        if answer:
            with st.spinner("Scoring your answer..."):
                session.submit(answer)
            st.rerun()
        b1, b2 = st.columns(2)
        if b1.button("Skip question"):
            session.skip()
            st.rerun()
        if b2.button("End interview"):
            session.end()
            st.rerun()

    if session.done:
        show_summary(session)


def show_summary(session):
    summary = session.summary()
    st.subheader("Interview summary")
    if not summary["answered"]:
        st.write("No questions were answered.")
    else:
        a, b = st.columns(2)
        a.metric("Average score", f"{summary['average']}/10")
        b.metric("Answered / skipped", f"{summary['answered']} / {summary['skipped']}")
        st.write(f"**Verdict:** {summary['readiness']}")
        if summary["estimate"]:
            st.caption("Some scores are keyword-based estimates, not AI scores.")
        if summary["by_type"]:
            st.write("By type: " + ", ".join(f"{t} {v}" for t, v in summary["by_type"].items()))
        if summary["strong_topics"]:
            st.write("**Strong:** " + "; ".join(summary["strong_topics"]))
        if summary["weak_topics"]:
            st.write("**Practise first:** " + "; ".join(summary["weak_topics"]))
        if summary["most_missed"]:
            st.write("**Points you often missed:** " + "; ".join(summary["most_missed"]))

    weak = [r["question"] for r in session.results if not r.get("skipped") and r["score"] < 6]
    c1, c2 = st.columns(2)
    if weak and c1.button("Practise weak topics again"):
        S.interview = InterviewSession(S.resume, analysis["jd"], ask_fn=ask_fn, questions=weak)
        st.rerun()
    if c2.button("New interview"):
        S.interview = None
        st.rerun()
    st.download_button("Download transcript (.txt)", session.transcript(), file_name="hirequill_interview.txt")


if view == "Match details":
    show_details()
elif view == "Gap report":
    show_gap_report()
else:
    show_interview()

# ------------------------------------------------------------------ re-score
st.divider()
with st.expander("Improved your resume? Re-score it against the same job"):
    st.caption("Upload the new PDF to see how the score changes. The job description stays the same.")
    new_pdf = st.file_uploader("Improved resume (PDF)", type=["pdf"], key="rescore_pdf")
    rescored = False
    if st.button("Re-score"):
        try:
            if new_pdf is None:
                raise pl.InputProblem("Upload the improved PDF first.")
            run_analysis(pl.resume_from_pdf(new_pdf.getvalue()), analysis["jd"], f"Try {len(S.history) + 1}", reset=False)
            rescored = True
        except pl.InputProblem as problem:
            st.error(str(problem))
        except Exception:
            st.error("Something went wrong while re-scoring. Please try again.")
    if rescored:
        st.rerun()      # redraw the score card with the new numbers
    if len(S.history) > 1:
        st.write("**Your tries**")
        rows = ["| Try | Match | Skills | Meaning |", "|---|---|---|---|"]
        rows += [f"| {h['label']} | {h['final']}% | {h['skills']}% | {h['meaning']}% |" for h in S.history]
        st.markdown("\n".join(rows))
