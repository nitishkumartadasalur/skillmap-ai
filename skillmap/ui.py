"""Styling and small HTML components for the Streamlit app.

All dynamic text is passed through ``html.escape``. HTML strings are built
without newlines or indentation so Streamlit's Markdown parser never treats
them as code blocks.
"""

from __future__ import annotations

import html

from .skills_db import CATEGORIES, CATEGORY_OF

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
  --bg: #0A1020;
  --surface: #111A2E;
  --surface-2: #16223B;
  --border: #243352;
  --text: #E7ECF7;
  --muted: #93A0BD;
  --indigo: #6366F1;
  --indigo-light: #818CF8;
  --green: #34D399;
  --amber: #F59E0B;
  --rose: #FB7185;
}

.stApp, .stMarkdown, .stApp p, .stApp label, .stApp button, .stApp input, .stApp textarea,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp li {
  font-family: 'Plus Jakarta Sans', Inter, system-ui, -apple-system, 'Segoe UI', sans-serif;
}
.stApp { background: radial-gradient(1200px 500px at 12% -10%, #17224a 0%, var(--bg) 55%); color: var(--text); }
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 1180px; }

section[data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--border); }

/* Cards: any bordered Streamlit container */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--surface);
  border: 1px solid var(--border) !important;
  border-radius: 14px;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] { height: 44px; padding: 0 16px; color: var(--muted); font-weight: 600; border-radius: 8px 8px 0 0; }
.stTabs [aria-selected="true"] { color: var(--text); }
.stTabs [data-baseweb="tab-highlight"] { background-color: var(--indigo-light); }

/* Buttons */
.stButton > button, .stDownloadButton > button {
  border-radius: 10px; border: 1px solid var(--border); background: var(--surface-2);
  color: var(--text); font-weight: 600; transition: border-color .15s, background .15s;
}
.stButton > button:hover, .stDownloadButton > button:hover { border-color: var(--indigo-light); color: #fff; }
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible { outline: 2px solid var(--indigo-light); outline-offset: 2px; }
.stButton > button[kind="primary"] { background: var(--indigo); border-color: var(--indigo); color: #fff; }
.stButton > button[kind="primary"]:hover { background: #7376f3; border-color: #7376f3; }

/* Brand header */
.brand { display: flex; align-items: center; gap: 14px; margin-bottom: 4px; }
.brand-mark { width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(145deg, #6366F1, #4338CA);
  display: grid; place-items: center; box-shadow: 0 6px 24px rgba(99,102,241,.35); }
.brand h1 { margin: 0; font-size: 1.75rem; font-weight: 800; letter-spacing: -0.02em; color: var(--text); padding: 0; }
.brand-sub { color: var(--muted); margin: 2px 0 22px 58px; font-size: .98rem; max-width: 60ch; }

/* Result hero */
.hero { display: flex; align-items: center; gap: 28px; padding: 26px 28px; border-radius: 16px; flex-wrap: wrap;
  background: linear-gradient(135deg, #1b2450 0%, #111A2E 70%); border: 1px solid #2c3a63; }
.ring { width: 132px; height: 132px; border-radius: 50%; flex: none; display: grid; place-items: center; background: #1B2744; }
.ring-inner { width: 102px; height: 102px; border-radius: 50%; background: var(--surface); display: grid; place-items: center; }
.ring-val { font-size: 2rem; font-weight: 800; color: var(--text); letter-spacing: -0.02em; }
.ring-val small { font-size: 1rem; font-weight: 600; color: var(--muted); margin-left: 1px; }
.hero-body { flex: 1; min-width: 240px; }
.hero-label { color: var(--muted); font-size: .9rem; font-weight: 600; margin: 0 0 4px; }
.hero-title { font-size: 1.55rem; font-weight: 800; margin: 0 0 14px; line-height: 1.25; letter-spacing: -0.01em; color: var(--text); }
.hero-stats { display: flex; gap: 12px; flex-wrap: wrap; }
.hero-stat { background: rgba(10,16,32,.55); border: 1px solid var(--border); border-radius: 10px; padding: 8px 14px; }
.hero-stat b { display: block; font-size: 1.15rem; color: var(--text); }
.hero-stat span { font-size: .8rem; color: var(--muted); }

/* KPI cards */
.kpi { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 16px 18px; height: 100%; }
.kpi-label { color: var(--muted); font-size: .85rem; font-weight: 600; }
.kpi-value { font-size: 1.7rem; font-weight: 800; color: var(--text); margin-top: 2px; letter-spacing: -0.02em; overflow-wrap: anywhere; }
.kpi-sub { color: var(--muted); font-size: .8rem; margin-top: 2px; }

/* Skill chips */
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 14px; }
.chip { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: .84rem; font-weight: 600; border: 1px solid transparent; }
.chip-ok { background: rgba(52,211,153,.12); color: var(--green); border-color: rgba(52,211,153,.35); }
.chip-miss { background: rgba(251,113,133,.12); color: var(--rose); border-color: rgba(251,113,133,.35); }
.chip-pref { background: rgba(245,158,11,.12); color: var(--amber); border-color: rgba(245,158,11,.35); }
.chip-neutral { background: rgba(129,140,248,.12); color: var(--indigo-light); border-color: rgba(129,140,248,.35); }
.group-title { color: var(--muted); font-weight: 600; font-size: .86rem; margin: 10px 0 0; }
.empty-note { color: var(--muted); font-size: .9rem; margin: 6px 0 14px; }

/* Suggestion cards */
.tip { background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--indigo); border-radius: 12px; padding: 14px 18px; margin: 0 0 12px; }
.tip-high { border-left-color: var(--rose); }
.tip-medium { border-left-color: var(--amber); }
.tip-low { border-left-color: var(--indigo-light); }
.tip-head { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; flex-wrap: wrap; }
.tip-title { font-weight: 700; color: var(--text); }
.tip-area { color: var(--muted); font-size: .8rem; }
.tip p { margin: 0; color: #C3CCE0; font-size: .93rem; line-height: 1.55; max-width: 80ch; }
.badge { font-size: .72rem; font-weight: 700; padding: 2px 9px; border-radius: 999px; }
.badge-high { background: rgba(251,113,133,.15); color: var(--rose); }
.badge-medium { background: rgba(245,158,11,.15); color: var(--amber); }
.badge-low { background: rgba(129,140,248,.15); color: var(--indigo-light); }

/* Empty state */
.empty { text-align: center; padding: 56px 24px; border: 1px dashed var(--border); border-radius: 16px; background: rgba(17,26,46,.6); }
.empty h3 { margin: 0 0 6px; color: var(--text); font-weight: 700; }
.empty p { margin: 0 auto; color: var(--muted); max-width: 52ch; }

.note { color: var(--muted); font-size: .86rem; line-height: 1.5; }
.legend { display: flex; gap: 16px; flex-wrap: wrap; color: var(--muted); font-size: .84rem; margin: 2px 0 8px; }
.legend i { display: inline-block; width: 11px; height: 11px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; }

@media (max-width: 640px) {
  .hero { padding: 20px; gap: 18px; }
  .brand-sub { margin-left: 0; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>
"""

_LOGO = (
    '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<circle cx="6" cy="7" r="2.4" fill="#fff"/><circle cx="18" cy="6" r="2.4" fill="#fff" fill-opacity=".75"/>'
    '<circle cx="12" cy="18" r="2.4" fill="#fff"/>'
    '<path d="M7.7 8.6 10.6 16M16.4 7.9 13.4 16M8.4 6.8h7.2" stroke="#fff" stroke-opacity=".7" stroke-width="1.4" stroke-linecap="round"/>'
    "</svg>"
)


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def header() -> str:
    return (
        f'<div class="brand"><div class="brand-mark">{_LOGO}</div><h1>SkillMap AI</h1></div>'
        '<p class="brand-sub">Resume matcher and skill gap analyzer. See which jobs fit your resume, '
        "which skills you already show, and where the gaps are.</p>"
    )


def hero(title: str, overall_pct: float, text_pct: float, coverage_pct: float | None, matched: int, missing_required: int) -> str:
    cov = "n/a" if coverage_pct is None else f"{coverage_pct:.0f}%"
    return (
        '<div class="hero">'
        f'<div class="ring" style="background:conic-gradient(#818CF8 {max(0.0, min(100.0, overall_pct)):.1f}%,#1B2744 0)">'
        f'<div class="ring-inner"><span class="ring-val">{overall_pct:.0f}<small>%</small></span></div></div>'
        '<div class="hero-body">'
        '<p class="hero-label">Best match</p>'
        f'<p class="hero-title">{e(title)}</p>'
        '<div class="hero-stats">'
        f'<div class="hero-stat"><b>{text_pct:.0f}%</b><span>Text similarity</span></div>'
        f'<div class="hero-stat"><b>{cov}</b><span>Skill coverage</span></div>'
        f'<div class="hero-stat"><b>{matched}</b><span>Skills matched</span></div>'
        f'<div class="hero-stat"><b>{missing_required}</b><span>Required skills missing</span></div>'
        "</div></div></div>"
    )


def kpi(label: str, value: object, sub: str = "") -> str:
    sub_html = f'<div class="kpi-sub">{e(sub)}</div>' if sub else ""
    return f'<div class="kpi"><div class="kpi-label">{e(label)}</div><div class="kpi-value">{e(value)}</div>{sub_html}</div>'


def chips(skills: list[str], kind: str = "neutral") -> str:
    if not skills:
        return ""
    return '<div class="chips">' + "".join(f'<span class="chip chip-{kind}">{e(s)}</span>' for s in skills) + "</div>"


def skills_by_category(skills: dict[str, int]) -> str:
    parts = []
    for category in [*CATEGORIES, "Other"]:
        group = [s for s in skills if CATEGORY_OF.get(s, "Other") == category]
        if group:
            parts.append(f'<p class="group-title">{e(category)}</p>' + chips(group, "neutral"))
    return "".join(parts)


def tip(priority: str, area: str, title: str, detail: str) -> str:
    p = priority.lower()
    return (
        f'<div class="tip tip-{p}"><div class="tip-head"><span class="badge badge-{p}">{e(priority)}</span>'
        f'<span class="tip-title">{e(title)}</span><span class="tip-area">{e(area)}</span></div>'
        f"<p>{e(detail)}</p></div>"
    )


def empty_state(title: str, body: str) -> str:
    return f'<div class="empty"><h3>{e(title)}</h3><p>{e(body)}</p></div>'


def gap_legend() -> str:
    return (
        '<div class="legend">'
        '<span><i style="background:#34D399"></i>Matched</span>'
        '<span><i style="background:#FB7185"></i>Missing, required</span>'
        '<span><i style="background:#F59E0B"></i>Missing, preferred</span>'
        '<span><i style="background:#111A2E;border:1px solid #243352"></i>Not requested</span>'
        "</div>"
    )
