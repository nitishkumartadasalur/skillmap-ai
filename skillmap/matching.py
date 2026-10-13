"""Scoring: TF-IDF cosine similarity plus skill coverage."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .extraction import JobSkill
from .skills_db import SKILL_ALIASES

#: Job-post boilerplate that carries no signal about fit.
_EXTRA_STOP_WORDS = {
    "experience", "experienced", "years", "year", "team", "teams", "work", "working", "works",
    "ability", "able", "strong", "role", "roles", "company", "looking", "join", "including",
    "etc", "will", "opportunity", "responsibilities", "responsibility", "requirements",
    "requirement", "skills", "skill", "knowledge", "preferred", "required", "plus", "nice",
    "benefits", "salary", "location", "position", "candidate", "candidates", "environment",
    "based", "related", "excellent", "good", "understanding", "using", "use", "new", "help",
    "across", "build", "building", "ideal", "must", "should", "least", "minimum", "degree",
    "bachelor", "equivalent", "remote", "hybrid", "full", "time", "apply", "us", "our", "you",
    "your", "we", "clear", "great", "like", "also", "well", "within", "needs", "need",
}
_STOP_WORDS = sorted(ENGLISH_STOP_WORDS | _EXTRA_STOP_WORDS)

# Make symbol-heavy skill names survive tokenisation ("c++" -> "cpp").
_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"c\+\+"), " cpp "),
    (re.compile(r"c#"), " csharp "),
    (re.compile(r"(?<![a-z0-9])\.net\b"), " dotnet "),
    (re.compile(r"ci\s*/\s*cd"), " cicd "),
    (re.compile(r"a\s*/\s*b\b"), " ab "),
    (re.compile(r"(\w)\.js\b"), r"\1js"),
    (re.compile(r"scikit[\s\-]learn"), " scikitlearn "),
    (re.compile(r"pl\s*/\s*sql"), " plsql "),
    (re.compile(r"https?://\S+|www\.\S+|\S+@\S+\.\S+"), " "),
]


def preprocess(text: str) -> str:
    """Lower-case, protect skill symbols, and strip punctuation."""
    text = text.lower()
    for pattern, replacement in _REPLACEMENTS:
        text = pattern.sub(replacement, text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = text.replace("_", " ")
    return re.sub(r"\s+", " ", text).strip()


def _skill_tokens() -> set[str]:
    tokens: set[str] = set()
    for skill, aliases in SKILL_ALIASES.items():
        for name in [skill, *aliases]:
            tokens.update(preprocess(name).split())
    return tokens


_SKILL_TOKENS = _skill_tokens()


@dataclass
class TfidfResult:
    similarities: list[float]  # 0..1, one per job
    missing_keywords: list[list[str]]  # prominent job terms absent from the resume


def tfidf_similarity(
    resume_text: str,
    job_texts: list[str],
    top_keywords: int = 8,
    job_titles: list[str] | None = None,
) -> TfidfResult:
    """Cosine similarity between the resume and each job in TF-IDF space.

    The vectoriser is fitted on the resume and all jobs together, using
    unigrams and bigrams with sublinear term frequency. Vectors are L2
    normalised, so cosine similarity is the dot product.
    """
    n_jobs = len(job_texts)
    empty = TfidfResult([0.0] * n_jobs, [[] for _ in range(n_jobs)])
    docs = [preprocess(resume_text)] + [preprocess(t) for t in job_texts]
    if not docs[0]:
        return empty

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words=_STOP_WORDS,
        sublinear_tf=True,
        token_pattern=r"(?u)\b[^\W\d_]\w+\b",
    )
    try:
        matrix = vectorizer.fit_transform(docs)
    except ValueError:  # empty vocabulary: nothing but stop words
        return empty

    sims = cosine_similarity(matrix[0], matrix[1:]).ravel()
    terms = vectorizer.get_feature_names_out()
    resume_row = matrix[0].toarray().ravel()

    keywords: list[list[str]] = []
    for i in range(n_jobs):
        row = matrix[i + 1].toarray().ravel()
        counts = Counter(docs[i + 1].split())
        title_terms = set(preprocess(job_titles[i]).split()) if job_titles else set()
        order = row.argsort()[::-1]
        picked: list[str] = []
        for idx in order:
            if row[idx] <= 0 or len(picked) >= top_keywords:
                break
            term = str(terms[idx])
            if resume_row[idx] > 0 or " " in term or len(term) < 4:
                continue
            if term in _SKILL_TOKENS or term.isdigit() or term in title_terms:
                continue
            if counts[term] < 2:  # "prominent" means the posting repeats it
                continue
            picked.append(term)
        keywords.append(picked)

    return TfidfResult([float(max(0.0, min(1.0, s))) for s in sims], keywords)


#: A missing "nice to have" counts for less than a missing requirement.
IMPORTANCE_WEIGHT = {"required": 1.0, "preferred": 0.5}


@dataclass
class CoverageResult:
    coverage: float | None  # None when the job lists no recognised skills
    matched: list[str]
    missing_required: list[str]
    missing_preferred: list[str]


def skill_coverage(resume_skills: dict[str, int], job_skills: dict[str, JobSkill]) -> CoverageResult:
    """Share of the job's skills (weighted by importance) found on the resume."""
    matched: list[str] = []
    missing_required: list[str] = []
    missing_preferred: list[str] = []
    total = got = 0.0
    for skill, info in job_skills.items():
        weight = IMPORTANCE_WEIGHT[info.importance]
        total += weight
        if skill in resume_skills:
            got += weight
            matched.append(skill)
        elif info.importance == "required":
            missing_required.append(skill)
        else:
            missing_preferred.append(skill)
    coverage = (got / total) if total else None
    return CoverageResult(coverage, matched, missing_required, missing_preferred)


def blend(text_similarity: float, coverage: float | None, skill_weight: float) -> float:
    """Overall match = (1 - w) * TF-IDF similarity + w * skill coverage.

    If the job lists no recognised skills there is nothing to blend, so the
    overall score is the TF-IDF similarity alone.
    """
    if coverage is None:
        return text_similarity
    w = max(0.0, min(1.0, skill_weight))
    return (1.0 - w) * text_similarity + w * coverage
