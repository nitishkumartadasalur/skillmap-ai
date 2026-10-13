"""Resume improvement suggestions that never invent experience.

Every suggestion about a skill gap is conditional: it tells the candidate to
add a skill only if they have genuinely used it, and otherwise to leave it off.
Nothing here generates resume bullets, employers, dates, or qualifications.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd

from .analysis import AnalysisResult, JobMatch
from .skills_db import related_skills

PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}

NO_INVENTION_NOTE = (
    "These suggestions only point at wording, structure, and gaps. Add a skill or "
    "achievement to your resume only if it is true and you could discuss it in an interview."
)


@dataclass(frozen=True)
class Suggestion:
    priority: str  # High / Medium / Low
    area: str
    title: str
    detail: str


def _join(items: list[str], limit: int = 6) -> str:
    shown = items[:limit]
    extra = len(items) - len(shown)
    text = ", ".join(shown)
    return f"{text} and {extra} more" if extra > 0 else text


# --------------------------------------------------------------------------
# Job-specific suggestions
# --------------------------------------------------------------------------
def build_job_suggestions(match: JobMatch, resume_skills: dict[str, int]) -> list[Suggestion]:
    out: list[Suggestion] = []

    for i, skill in enumerate(match.missing_required[:6]):
        rel = related_skills(skill, resume_skills)
        transferable = (
            f" Your resume already shows {_join(rel, 3)}; if that work overlapped with {skill}, "
            f"describe the overlap accurately rather than claiming {skill} itself."
            if rel
            else ""
        )
        out.append(
            Suggestion(
                "High" if i < 3 else "Medium",
                "Skill gap",
                f"Required skill not found: {skill}",
                f"This posting asks for {skill}, and it does not appear on your resume. Add it only if you "
                f"have genuinely used it: name the project, your role, and what it achieved.{transferable} "
                f"If you have not used it, leave it off and consider a small real project or course so you "
                f"can add it truthfully later.",
            )
        )
    if len(match.missing_required) > 6:
        rest = match.missing_required[6:]
        out.append(
            Suggestion(
                "Medium",
                "Skill gap",
                f"More required skills not found: {_join(rest, 8)}",
                "Review these the same way: mention each only if you have real experience with it.",
            )
        )

    if match.missing_preferred:
        out.append(
            Suggestion(
                "Low",
                "Skill gap",
                f"Nice-to-have skills not found: {_join(match.missing_preferred, 8)}",
                "These are listed as preferred, so gaps here matter less. Mention them only where they "
                "reflect experience you actually have.",
            )
        )

    thin = [s for s in match.matched if match.job_skills[s].importance == "required" and resume_skills.get(s, 0) == 1]
    if thin:
        out.append(
            Suggestion(
                "Medium",
                "Evidence",
                f"Required skills mentioned only once: {_join(thin, 6)}",
                "These are required for this role and appear a single time on your resume. If you used them "
                "in real projects, add a bullet showing what you built and the result. If not, leave them as they are.",
            )
        )

    if len(match.matched) >= 3:
        top = [s for s in match.matched if match.job_skills[s].importance == "required"][:4] or match.matched[:4]
        out.append(
            Suggestion(
                "Medium",
                "Positioning",
                "Lead with your matching strengths",
                f"Your resume covers {len(match.matched)} skills this posting asks for, including {_join(top, 4)}. "
                f"Make them easy to spot in your summary and skills section, and tie each to a specific project. "
                f"Keep the claims exactly as strong as the work behind them.",
            )
        )

    if match.missing_keywords:
        out.append(
            Suggestion(
                "Low",
                "Keywords",
                f"Terms this posting emphasizes: {_join(match.missing_keywords, 6)}",
                "These words stand out in the posting but not on your resume. Use one only where it truthfully "
                "describes work you have already done, for example matching the posting's wording for a task you "
                "performed. Do not add terms for experience you lack.",
            )
        )

    if match.skill_coverage is None:
        out.append(
            Suggestion(
                "Low",
                "Analysis",
                "No known skills detected in this job description",
                "The skill list did not recognise any technologies in this posting, so its score is based on "
                "text similarity alone. Check that the full description was pasted.",
            )
        )

    return sorted(out, key=lambda s: PRIORITY_ORDER[s.priority])


# --------------------------------------------------------------------------
# General resume checks (independent of any job)
# --------------------------------------------------------------------------
_SECTION_PATTERNS = {
    "summary": re.compile(r"^\s*(professional\s+|career\s+)?(summary|profile|objective|about me)\b", re.I | re.M),
    "skills": re.compile(r"^\s*(technical\s+|core\s+|key\s+)?(skills|technologies|tech stack)\b", re.I | re.M),
    "experience": re.compile(r"^\s*(professional\s+|work\s+|relevant\s+)?(experience|employment)\b", re.I | re.M),
    "projects": re.compile(r"^\s*(selected\s+|personal\s+|key\s+)?projects\b", re.I | re.M),
    "education": re.compile(r"^\s*education\b", re.I | re.M),
}
_BULLET_LINE = re.compile(r"^\s*[-*\u2022\u25cf\u25aa\u25e6\u2013]\s+(.*\S)", re.M)
_WEAK_PHRASES = re.compile(
    r"\b(responsible for|worked on|helped with|helped to|assisted with|duties included|tasked with)\b", re.I
)


def resume_stats(text: str) -> dict[str, float | int | bool]:
    bullets = _BULLET_LINE.findall(text)
    with_numbers = sum(1 for b in bullets if re.search(r"\d", b))
    return {
        "words": len(re.findall(r"\w+", text)),
        "bullets": len(bullets),
        "bullets_with_numbers": with_numbers,
        "weak_phrases": len(_WEAK_PHRASES.findall(text)),
        **{f"has_{name}": bool(p.search(text)) for name, p in _SECTION_PATTERNS.items()},
    }


def general_suggestions(resume_text: str) -> list[Suggestion]:
    s = resume_stats(resume_text)
    out: list[Suggestion] = []

    if s["words"] < 150:
        out.append(
            Suggestion(
                "Medium",
                "Structure",
                f"The resume is short ({s['words']} words)",
                "Short resumes give matching little to work with. Where you have real work to describe, add "
                "what you did, the tools you used, and the outcome.",
            )
        )
    elif s["words"] > 900:
        out.append(
            Suggestion(
                "Low",
                "Structure",
                f"The resume is long ({s['words']} words)",
                "Consider trimming older or less relevant details so the strongest, most relevant work stands out.",
            )
        )

    if not s["has_skills"]:
        out.append(
            Suggestion(
                "Medium",
                "Structure",
                "No skills section found",
                "A clear skills section helps readers and applicant tracking systems find your tools quickly. "
                "List only tools you could discuss in an interview.",
            )
        )
    if not s["has_experience"] and not s["has_projects"]:
        out.append(
            Suggestion(
                "Medium",
                "Structure",
                "No experience or projects section found",
                "Add a section for work, internships, or projects so your skills are backed by evidence. Use only real work.",
            )
        )
    if not s["has_summary"]:
        out.append(
            Suggestion(
                "Low",
                "Structure",
                "No summary found",
                "A two or three line summary can state your target role and strengths. Draw it only from facts "
                "already in your resume.",
            )
        )

    if s["bullets"] >= 4 and s["bullets_with_numbers"] / s["bullets"] < 0.25:
        out.append(
            Suggestion(
                "Medium",
                "Impact",
                "Few bullets include measurable results",
                f"Only {s['bullets_with_numbers']} of {s['bullets']} bullets contain a number. Where you have real "
                "figures (time saved, volume, accuracy, users), add them. If you do not have exact numbers, describe "
                "the scope in plain words rather than estimating.",
            )
        )
    elif s["bullets"] == 0 and s["words"] > 200:
        out.append(
            Suggestion(
                "Low",
                "Structure",
                "No bullet points detected",
                "Short bullets that start with an action verb are easier to scan than paragraphs. "
                "If your file has bullets, they may have been lost when the text was extracted.",
            )
        )

    if s["weak_phrases"] >= 2:
        out.append(
            Suggestion(
                "Low",
                "Wording",
                f"Passive phrasing appears {s['weak_phrases']} times",
                "Phrases like 'responsible for' or 'worked on' hide what you personally did. Replace them with a "
                "verb that describes your actual contribution, such as built, designed, analysed, or led, "
                "but only when it is accurate.",
            )
        )

    return sorted(out, key=lambda x: PRIORITY_ORDER[x.priority])


# --------------------------------------------------------------------------
# Export helper
# --------------------------------------------------------------------------
def all_suggestions_df(result: AnalysisResult, resume_text: str) -> pd.DataFrame:
    rows = []
    for sug in general_suggestions(resume_text):
        rows.append(("All jobs", sug))
    for match in result.matches:
        for sug in build_job_suggestions(match, result.resume_skills):
            rows.append((match.title, sug))
    return pd.DataFrame(
        [
            {"Job": job, "Priority": s.priority, "Area": s.area, "Suggestion": s.title, "Details": s.detail}
            for job, s in rows
        ],
        columns=["Job", "Priority", "Area", "Suggestion", "Details"],
    )
