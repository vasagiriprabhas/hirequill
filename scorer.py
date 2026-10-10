"""Day 3: meaning-based score and the final combined score.

Skill score  = how many of the job's required skills your resume shows (extractor.py).
Meaning score = does your resume talk about the same things the job describes, even in
                different words ("data visualization" vs "dashboards").
Final score  = 60% skills + 40% meaning.
"""
import re

import numpy as np

from extractor import extract_skills

WEIGHTS = {"skills": 0.6, "meaning": 0.4}

# Score bands decide what the app does next.
BANDS = (
    (70, "high", "Strong match. Start the mock interview."),
    (40, "medium", "Partial match. Show the gap report; the interview is optional."),
    (0, "low", "Weak match. Show the gap report and a learning plan first."),
)

# Raw similarity numbers are not percentages. These (low, high) pairs stretch the raw
# similarity onto 0-100. They are starting values: tune them on Day 6 using real
# resume and job description pairs.
CALIBRATION = {"embedding": (0.20, 0.60), "tfidf": (0.00, 0.30)}

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model = None


def split_chunks(text: str, min_words: int = 3) -> list:
    """Cut text into short lines or sentences, which is what the models compare."""
    chunks = []
    for line in text.split("\n"):
        line = re.sub(r"^[\s\-*•]+", "", line).strip()
        for piece in re.split(r"(?<=[.!?])\s+", line):
            if len(piece.split()) >= min_words:
                chunks.append(piece)
    return chunks


def _similarity_embedding(resume_chunks: list, jd_chunks: list):
    """Free local AI model (about 90 MB, downloaded once on first use)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    resume_vecs = _model.encode(resume_chunks, normalize_embeddings=True, show_progress_bar=False)
    jd_vecs = _model.encode(jd_chunks, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(jd_vecs) @ np.asarray(resume_vecs).T  # rows = JD chunks


def _similarity_tfidf(resume_chunks: list, jd_chunks: list):
    """Lighter fallback that compares shared words and phrases. No download needed."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
    matrix = vectorizer.fit_transform(resume_chunks + jd_chunks)
    resume_part, jd_part = matrix[: len(resume_chunks)], matrix[len(resume_chunks):]
    return (jd_part @ resume_part.T).toarray()


def coverage(similarity) -> float:
    """For each job line, find the best matching resume line, then average them."""
    return float(np.asarray(similarity).max(axis=1).mean())


def meaning_score(resume_text: str, jd_text: str, backend: str = "auto") -> dict:
    """backend: 'auto' (AI model, falling back to tfidf), 'embedding', or 'tfidf'."""
    resume_chunks = split_chunks(resume_text)
    jd_chunks = split_chunks(jd_text)
    # Only judge job lines that mention a skill. Lines like "About the company"
    # would otherwise drag the score down for no reason.
    jd_chunks = [c for c in jd_chunks if extract_skills(c)] or jd_chunks

    if not resume_chunks or not jd_chunks:
        return {"score": 0.0, "raw": 0.0, "backend": "none", "lines_checked": 0,
                "note": "Not enough text to compare."}

    note, used, similarity = "", None, None
    if backend in ("auto", "embedding"):
        try:
            similarity, used = _similarity_embedding(resume_chunks, jd_chunks), "embedding"
        except Exception as error:  # missing library, no internet, model not downloaded
            if backend == "embedding":
                raise
            note = f"AI model unavailable ({type(error).__name__}); used the lighter word-based method."
    if similarity is None:
        similarity, used = _similarity_tfidf(resume_chunks, jd_chunks), "tfidf"

    raw = coverage(similarity)
    low, high = CALIBRATION[used]
    score = round(float(np.clip((raw - low) / (high - low), 0, 1)) * 100, 1)
    return {"score": score, "raw": round(raw, 3), "backend": used,
            "lines_checked": len(jd_chunks), "note": note}


def final_score(skill_pct: float, meaning_pct: float) -> dict:
    total = round(WEIGHTS["skills"] * skill_pct + WEIGHTS["meaning"] * meaning_pct, 1)
    for floor, band, advice in BANDS:
        if total >= floor:
            return {"score": total, "band": band, "advice": advice}
