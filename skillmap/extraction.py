"""Rule-based technical skill extraction.

Skills are found with word-boundary regexes built from the taxonomy in
``skills_db``. Boundaries treat ``+`` and ``#`` as part of a word, so ``C++``
and ``C#`` match correctly while ``Java`` never matches inside ``JavaScript``
and ``SQL`` never matches inside ``MySQL`` or ``NoSQL``.

For job descriptions we also record whether a skill looks *required* or
*preferred* ("nice to have", "bonus", "a plus"...), because a missing
nice-to-have matters less than a missing requirement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .skills_db import CATEGORY_OF, CONTEXT_SKILLS, NOT_FOLLOWED_BY, SKILL_ALIASES

_LOOKBEHIND = r"(?<![a-z0-9+#])"
_LOOKAHEAD = r"(?![a-z0-9+#])"


def _alias_pattern(alias: str) -> str:
    """Regex for one alias; spaces and hyphens are interchangeable."""
    parts = [p for p in re.split(r"[\s\-]+", alias) if p]
    return r"[\s\-]*".join(re.escape(p) for p in parts)


def _build_patterns() -> dict[str, re.Pattern[str]]:
    compiled: dict[str, re.Pattern[str]] = {}
    for skill, aliases in SKILL_ALIASES.items():
        if not aliases:
            continue
        alts = sorted({_alias_pattern(a) for a in aliases}, key=len, reverse=True)
        tail = _LOOKAHEAD
        if skill in NOT_FOLLOWED_BY:
            tail += f"(?!{NOT_FOLLOWED_BY[skill]})"
        compiled[skill] = re.compile(_LOOKBEHIND + "(?:" + "|".join(alts) + ")" + tail)
    return compiled


def _context_pattern(word: str) -> re.Pattern[str]:
    """Case-sensitive match for an ambiguous word such as ``Go`` or ``R``.

    It only counts when the word sits in a list ("Python, R, SQL"), ends a
    sentence or line, or is followed by "programming"/"language", so ordinary
    prose ("Go to market", "R&D", "Excel at") is ignored.
    """
    tail = (
        r"(?=\s*[,;/|)]"
        r"|\s*\.(?:\s|$)"
        r"|\s*$"
        r"|\s+(?:programming|language|lang)\b"
        r"|\s+(?:and|or)\s+[A-Z])"
    )
    return re.compile(r"(?<![\w+#.\-])" + re.escape(word) + tail, re.MULTILINE)


_PATTERNS = _build_patterns()
_CONTEXT = {skill: _context_pattern(skill) for skill in CONTEXT_SKILLS}
# "ML" is an abbreviation only when written in capitals ("5 ml" is a volume).
_CONTEXT["Machine Learning"] = re.compile(r"(?<![\w+#.\-])ML(?![\w+#&])")


def _normalise(text: str) -> str:
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2011", "-")
    return text.replace("\u00a0", " ").replace("\u2019", "'")


def find_skills(text: str, only: set[str] | None = None) -> dict[str, int]:
    """Return ``{skill: mention_count}`` for every skill found in ``text``."""
    text = _normalise(text)
    lowered = text.lower()
    found: dict[str, int] = {}
    names = set(_PATTERNS) | set(_CONTEXT)
    for skill in names:
        if only is not None and skill not in only:
            continue
        count = 0
        pattern = _PATTERNS.get(skill)
        if pattern is not None:
            count += len(pattern.findall(lowered))
        context = _CONTEXT.get(skill)
        if context is not None:
            count += len(context.findall(text))
        if count:
            found[skill] = count
    return found


def extract_resume_skills(text: str) -> dict[str, int]:
    """Skills found in a resume, mapped to how many times each is mentioned."""
    return dict(sorted(find_skills(text).items(), key=lambda kv: (-kv[1], kv[0])))


@dataclass(frozen=True)
class JobSkill:
    importance: str  # "required" or "preferred"
    mentions: int


_PREF_WORDS = (
    r"nice[- ]to[- ]haves?|preferred(?: qualifications| skills| experience)?"
    r"|bonus(?: points)?|good to haves?|pluses|desirable|optional"
)
_PREF_START = re.compile(rf"\W*(?:{_PREF_WORDS})\b", re.IGNORECASE)
_INLINE_PREF = re.compile(
    r"\b(?:nice[- ]to[- ]have|preferred|bonus|a plus|is a plus|are a plus|good to have|desirable|ideally|big plus)\b",
    re.IGNORECASE,
)
_REQ_HEADER = re.compile(
    r"\W*(?:key |minimum |basic |required )?(?:requirements?|responsibilit(?:y|ies)|qualifications?|must[- ]haves?"
    r"|what you(?:'ll| will) (?:do|bring|need)|about you|who you are|required skills|the role|about the role"
    r"|your responsibilities|what we(?:'re| are) looking for)\W*",
    re.IGNORECASE,
)
_BULLET = re.compile(r"^\s*(?:[-*\u2022\u25cf\u25aa\u2013]|\d+[.)])\s+")


def extract_job_skills(text: str) -> dict[str, JobSkill]:
    """Skills in a job description, tagged required or preferred."""
    text = _normalise(text)
    present = set(find_skills(text))
    if not present:
        return {}

    required: dict[str, int] = {}
    preferred: dict[str, int] = {}
    mode = "required"

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        is_bullet = bool(_BULLET.match(line))
        body = _BULLET.sub("", line)

        if not is_bullet and len(line) <= 80:
            if _PREF_START.match(body):
                mode = "preferred"
            elif _REQ_HEADER.fullmatch(body) or (body.endswith(":") and len(body) <= 60):
                mode = "required"

        # Classify sentence by sentence so "Build APIs. Kafka is a plus." only
        # marks Kafka as preferred.
        for sentence in re.split(r"(?<=[.;!?])\s+", body):
            importance = "preferred" if mode == "preferred" or _INLINE_PREF.search(sentence) else "required"
            bucket = preferred if importance == "preferred" else required
            for skill, count in find_skills(sentence, only=present).items():
                bucket[skill] = bucket.get(skill, 0) + count

    result: dict[str, JobSkill] = {}
    for skill in present:
        req, pref = required.get(skill, 0), preferred.get(skill, 0)
        if req:
            result[skill] = JobSkill("required", req + pref)
        elif pref:
            result[skill] = JobSkill("preferred", pref)
    return dict(sorted(result.items(), key=lambda kv: (kv[1].importance != "required", -kv[1].mentions, kv[0])))


def category_of(skill: str) -> str:
    return CATEGORY_OF.get(skill, "Other")
