"""Run a full resume-vs-jobs analysis and expose the results as DataFrames."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .extraction import JobSkill, extract_job_skills, extract_resume_skills
from .matching import IMPORTANCE_WEIGHT, blend, skill_coverage, tfidf_similarity
from .skills_db import CATEGORIES, CATEGORY_OF


@dataclass
class JobMatch:
    rank: int
    title: str
    text_similarity: float  # 0..1
    skill_coverage: float | None  # 0..1, None if the job lists no known skills
    overall: float  # 0..1
    job_skills: dict[str, JobSkill]
    matched: list[str]
    missing_required: list[str]
    missing_preferred: list[str]
    missing_keywords: list[str] = field(default_factory=list)

    @property
    def missing(self) -> list[str]:
        return self.missing_required + self.missing_preferred


@dataclass
class AnalysisResult:
    resume_skills: dict[str, int]
    matches: list[JobMatch]  # sorted best to worst
    skill_weight: float

    # ---- lookups -------------------------------------------------------
    def match_for(self, title: str) -> JobMatch:
        for match in self.matches:
            if match.title == title:
                return match
        raise KeyError(title)

    # ---- tables --------------------------------------------------------
    def summary_df(self) -> pd.DataFrame:
        rows = []
        for m in self.matches:
            rows.append(
                {
                    "Rank": m.rank,
                    "Job": m.title,
                    "Overall match (%)": round(m.overall * 100, 1),
                    "Text similarity (%)": round(m.text_similarity * 100, 1),
                    "Skill coverage (%)": None if m.skill_coverage is None else round(m.skill_coverage * 100, 1),
                    "Matched skills": len(m.matched),
                    "Missing required": len(m.missing_required),
                    "Missing preferred": len(m.missing_preferred),
                    "Matched skill list": ", ".join(m.matched),
                    "Missing required list": ", ".join(m.missing_required),
                    "Missing preferred list": ", ".join(m.missing_preferred),
                }
            )
        return pd.DataFrame(rows)

    def gap_df(self) -> pd.DataFrame:
        rows = []
        for m in self.matches:
            for skill, info in m.job_skills.items():
                rows.append(
                    {
                        "Rank": m.rank,
                        "Job": m.title,
                        "Skill": skill,
                        "Category": CATEGORY_OF.get(skill, "Other"),
                        "Importance": info.importance.capitalize(),
                        "Status": "Matched" if skill in self.resume_skills else "Missing",
                        "Mentions in job": info.mentions,
                        "Mentions in resume": self.resume_skills.get(skill, 0),
                    }
                )
        columns = ["Rank", "Job", "Skill", "Category", "Importance", "Status", "Mentions in job", "Mentions in resume"]
        return pd.DataFrame(rows, columns=columns)

    def resume_skills_df(self) -> pd.DataFrame:
        rows = [
            {"Skill": s, "Category": CATEGORY_OF.get(s, "Other"), "Mentions": n}
            for s, n in self.resume_skills.items()
        ]
        return pd.DataFrame(rows, columns=["Skill", "Category", "Mentions"])

    def category_df(self, match: JobMatch) -> pd.DataFrame:
        """Per-category coverage for one job (only categories the job asks for)."""
        rows = []
        for category in CATEGORIES:
            wanted = [(s, i) for s, i in match.job_skills.items() if CATEGORY_OF.get(s) == category]
            if not wanted:
                continue
            total = sum(IMPORTANCE_WEIGHT[i.importance] for _, i in wanted)
            got = sum(IMPORTANCE_WEIGHT[i.importance] for s, i in wanted if s in self.resume_skills)
            rows.append(
                {
                    "Category": category,
                    "Job asks for": len(wanted),
                    "You have": sum(1 for s, _ in wanted if s in self.resume_skills),
                    "Coverage (%)": round(100 * got / total, 1),
                }
            )
        return pd.DataFrame(rows, columns=["Category", "Job asks for", "You have", "Coverage (%)"])

    def skill_matrix(self, max_rows: int = 30) -> pd.DataFrame:
        """Skills (rows) x jobs (columns) with status codes.

        0 = not requested, 1 = missing (preferred), 2 = missing (required),
        3 = matched.
        """
        demand: dict[str, int] = {}
        for m in self.matches:
            for skill in m.job_skills:
                demand[skill] = demand.get(skill, 0) + 1
        # Most-requested first; at equal demand, gaps before matches so truncation
        # drops the skills you already have rather than the ones you lack.
        skills = sorted(demand, key=lambda s: (-demand[s], s in self.resume_skills, s))[:max_rows]
        data: dict[str, list[int]] = {}
        for m in self.matches:
            column = []
            for skill in skills:
                info = m.job_skills.get(skill)
                if info is None:
                    column.append(0)
                elif skill in self.resume_skills:
                    column.append(3)
                else:
                    column.append(2 if info.importance == "required" else 1)
            data[m.title] = column
        return pd.DataFrame(data, index=pd.Index(skills, name="Skill"))

    def distinct_job_skills(self) -> int:
        return len({skill for m in self.matches for skill in m.job_skills})

    def top_missing_df(self, limit: int = 12) -> pd.DataFrame:
        """Skills missing from the resume, ranked by how many jobs ask for them."""
        counts: dict[str, list[int]] = {}
        for m in self.matches:
            for skill in m.missing:
                entry = counts.setdefault(skill, [0, 0])
                entry[0] += 1
                if skill in m.missing_required:
                    entry[1] += 1
        rows = [
            {
                "Skill": s,
                "Category": CATEGORY_OF.get(s, "Other"),
                "Jobs missing in": c[0],
                "Required in jobs": c[1],
            }
            for s, c in counts.items()
        ]
        df = pd.DataFrame(rows, columns=["Skill", "Category", "Jobs missing in", "Required in jobs"])
        if df.empty:
            return df
        df = df.sort_values(["Jobs missing in", "Required in jobs", "Skill"], ascending=[False, False, True])
        return df.head(limit).reset_index(drop=True)


def _unique_titles(titles: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for raw in titles:
        title = raw.strip() or "Untitled job"
        seen[title] = seen.get(title, 0) + 1
        out.append(title if seen[title] == 1 else f"{title} ({seen[title]})")
    return out


def analyze(resume_text: str, jobs: list[tuple[str, str]], skill_weight: float = 0.5) -> AnalysisResult:
    """Compare one resume against several job descriptions.

    ``jobs`` is a list of ``(title, description)``. ``skill_weight`` (0..1) is
    how much skill coverage counts in the overall score; the rest comes from
    TF-IDF cosine similarity.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("The resume is empty.")
    jobs = [(t, d) for t, d in jobs if d and d.strip()]
    if not jobs:
        raise ValueError("Add at least one job description.")

    titles = _unique_titles([t for t, _ in jobs])
    texts = [d for _, d in jobs]

    resume_skills = extract_resume_skills(resume_text)
    tfidf = tfidf_similarity(resume_text, texts, job_titles=titles)

    matches: list[JobMatch] = []
    for i, (title, text) in enumerate(zip(titles, texts)):
        job_skills = extract_job_skills(text)
        cov = skill_coverage(resume_skills, job_skills)
        sim = tfidf.similarities[i]
        matches.append(
            JobMatch(
                rank=0,
                title=title,
                text_similarity=sim,
                skill_coverage=cov.coverage,
                overall=blend(sim, cov.coverage, skill_weight),
                job_skills=job_skills,
                matched=cov.matched,
                missing_required=cov.missing_required,
                missing_preferred=cov.missing_preferred,
                missing_keywords=tfidf.missing_keywords[i],
            )
        )

    matches.sort(key=lambda m: (-m.overall, -m.text_similarity, m.title))
    for rank, match in enumerate(matches, start=1):
        match.rank = rank
    return AnalysisResult(resume_skills=resume_skills, matches=matches, skill_weight=skill_weight)
