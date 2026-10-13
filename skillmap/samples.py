"""Load the bundled sample resumes and job descriptions."""

from __future__ import annotations

from pathlib import Path

from .parsing import extract_text

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RESUME_DIR = DATA_DIR / "sample_resumes"
JOB_DIR = DATA_DIR / "sample_jobs"


_ACRONYMS = {"ml": "ML", "ai": "AI", "qa": "QA", "devops": "DevOps"}


def _pretty(stem: str) -> str:
    words = [w for w in stem.replace("_", " ").split() if not w.isdigit()]
    return " ".join(_ACRONYMS.get(w.lower(), w.capitalize()) for w in words)


def sample_resume_paths() -> dict[str, Path]:
    """``{label: path}`` for the bundled sample resumes (top-level .txt files)."""
    return {_pretty(p.stem): p for p in sorted(RESUME_DIR.glob("*.txt"))}


def sample_resume_labels() -> list[str]:
    return list(sample_resume_paths())


def read_sample_resume(label: str) -> str:
    return extract_text(sample_resume_paths()[label].name, sample_resume_paths()[label].read_bytes())


def sample_job_list() -> list[tuple[str, str]]:
    """``[(title, description)]`` read from ``data/sample_jobs``.

    The first line of each file is ``Title: ...``; the rest is the description.
    """
    jobs: list[tuple[str, str]] = []
    for path in sorted(JOB_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        first, _, rest = text.partition("\n")
        if first.lower().startswith("title:"):
            title, body = first.split(":", 1)[1].strip(), rest.strip()
        else:
            title, body = _pretty(path.stem), text
        jobs.append((title, body))
    return jobs
