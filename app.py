"""SkillMap AI: resume matcher and skill gap analyzer (Streamlit app).

Run with:  streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from skillmap import charts, ui
from skillmap.analysis import AnalysisResult, analyze
from skillmap.extraction import extract_resume_skills
from skillmap.parsing import MAX_FILE_BYTES, ParseError, extract_text
from skillmap.samples import read_sample_resume, sample_job_list, sample_resume_labels
from skillmap.suggestions import NO_INVENTION_NOTE, all_suggestions_df, build_job_suggestions, general_suggestions

st.set_page_config(page_title="SkillMap AI", page_icon="🧭", layout="wide", initial_sidebar_state="expanded")

MIN_JD_CHARS = 40
DEFAULT_SKILL_WEIGHT_PCT = 60


# --------------------------------------------------------------------------
# Small helpers that work across Streamlit versions
# --------------------------------------------------------------------------
def show_chart(fig, key: str | None = None) -> None:
    try:
        st.plotly_chart(fig, width="stretch", key=key, config={"displayModeBar": False})
    except Exception:  # older Streamlit: no width="stretch"
        st.plotly_chart(fig, use_container_width=True, key=key, config={"displayModeBar": False})


def show_df(df: pd.DataFrame, **kwargs) -> None:
    try:
        st.dataframe(df, width="stretch", hide_index=True, **kwargs)
    except Exception:  # older Streamlit
        st.dataframe(df, use_container_width=True, hide_index=True, **kwargs)


def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


@st.cache_data(show_spinner=False, max_entries=16)
def run_analysis(resume_text: str, jobs: tuple[tuple[str, str], ...], skill_weight: float) -> AnalysisResult:
    return analyze(resume_text, list(jobs), skill_weight)


# --------------------------------------------------------------------------
# Session state and callbacks (callbacks run before the next script run, so
# they may safely set widget values)
# --------------------------------------------------------------------------
def _init_state() -> None:
    ss = st.session_state
    if "jobs" not in ss:
        ss.jobs = [1]
        ss.next_job_id = 2
        ss.snapshot = None


def _drop_job_keys(job_id: int) -> None:
    st.session_state.pop(f"jt_{job_id}", None)
    st.session_state.pop(f"jd_{job_id}", None)


def _new_job_id() -> int:
    ss = st.session_state
    job_id = ss.next_job_id
    ss.next_job_id += 1
    ss.jobs.append(job_id)
    return job_id


def add_job() -> None:
    _new_job_id()


def remove_job(job_id: int) -> None:
    ss = st.session_state
    ss.jobs = [j for j in ss.jobs if j != job_id]
    _drop_job_keys(job_id)
    if not ss.jobs:
        _new_job_id()


def clear_jobs() -> None:
    ss = st.session_state
    for job_id in list(ss.jobs):
        _drop_job_keys(job_id)
    ss.jobs = []
    _new_job_id()


def load_sample_jobs() -> None:
    ss = st.session_state
    for job_id in list(ss.jobs):
        _drop_job_keys(job_id)
    ss.jobs = []
    for title, text in sample_job_list():
        job_id = _new_job_id()
        ss[f"jt_{job_id}"] = title
        ss[f"jd_{job_id}"] = text


_init_state()
st.markdown(ui.CSS, unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Scoring")
    skill_pct = st.slider(
        "Weight on skill coverage (%)",
        min_value=0,
        max_value=100,
        value=DEFAULT_SKILL_WEIGHT_PCT,
        step=5,
        key="skill_pct",
        help="Overall match blends TF-IDF text similarity with skill coverage. 0% uses text similarity only.",
    )
    st.caption(f"Overall match = {100 - skill_pct}% text similarity + {skill_pct}% skill coverage.")
    with st.expander("How scores work"):
        st.markdown(
            "- **Text similarity** is the cosine similarity between TF-IDF vectors of your resume and the job "
            "description (unigrams and bigrams). Raw values for real resumes are usually low, often 10 to 40%, "
            "so use it to compare jobs rather than as an absolute grade.\n"
            "- **Skill coverage** is the share of the job's recognised skills found on your resume. "
            "Required skills count fully and nice-to-haves count half.\n"
            "- Skills come from a built-in list of about 250 technologies, so a skill outside that list is not detected."
        )
    st.markdown("### Privacy")
    st.caption("Files are read in memory by this app and are not saved by it. Nothing is sent to an external service.")
    st.caption("Skill and suggestion text is rule-based. It never writes experience for you.")

# --------------------------------------------------------------------------
# Header + banner placeholder
# --------------------------------------------------------------------------
html(ui.header())
banner = st.empty()

tab_setup, tab_rank, tab_gap, tab_improve, tab_export = st.tabs(
    ["Setup", "Rankings", "Skill gap", "Improve resume", "Export"]
)

# --------------------------------------------------------------------------
# Setup tab
# --------------------------------------------------------------------------
resume_text = ""
resume_label = ""
with tab_setup:
    left, right = st.columns([1, 1.25], gap="large")

    # ---- Resume ---------------------------------------------------------
    with left:
        with st.container(border=True):
            st.subheader("Your resume")
            mode = st.radio(
                "Resume source",
                ["Upload file", "Paste text", "Use a sample"],
                horizontal=True,
                key="resume_mode",
                label_visibility="collapsed",
            )
            parse_error: str | None = None
            if mode == "Upload file":
                upload = st.file_uploader(
                    "Resume file",
                    type=["pdf", "docx", "txt"],
                    key="resume_file",
                    label_visibility="collapsed",
                    help=f"PDF, DOCX, or TXT up to {MAX_FILE_BYTES // (1024 * 1024)} MB. Scanned image PDFs are not supported.",
                )
                if upload is not None:
                    try:
                        resume_text = extract_text(upload.name, upload.getvalue())
                        resume_label = upload.name
                    except ParseError as exc:
                        parse_error = str(exc)
                else:
                    st.caption("PDF, DOCX, or TXT.")
            elif mode == "Paste text":
                resume_text = st.text_area(
                    "Resume text",
                    height=260,
                    key="resume_paste",
                    placeholder="Paste your resume text here",
                    label_visibility="collapsed",
                ).strip()
                resume_label = "Pasted text"
            else:
                labels = sample_resume_labels()
                choice = st.selectbox("Sample resume", labels, key="resume_sample")
                resume_text = read_sample_resume(choice)
                resume_label = f"Sample: {choice}"
                st.caption("A fictional resume bundled with the app.")

            if parse_error:
                st.error(parse_error)
            elif resume_text:
                skills = extract_resume_skills(resume_text)
                word_count = len(resume_text.split())
                st.success(f"Read {resume_label} ({word_count:,} words). Found {len(skills)} skills.")
                with st.expander("Skills found in your resume", expanded=False):
                    html(ui.skills_by_category(skills) or '<p class="empty-note">No known skills detected.</p>')
                with st.expander("Extracted text preview", expanded=False):
                    st.text(resume_text[:3000] + ("\n..." if len(resume_text) > 3000 else ""))

    # ---- Jobs -----------------------------------------------------------
    with right:
        with st.container(border=True):
            st.subheader("Job descriptions")
            b1, b2, b3 = st.columns(3)
            b1.button("Add job", key="btn_add_job", on_click=add_job)
            b2.button("Load sample jobs", key="btn_load_jobs", on_click=load_sample_jobs)
            b3.button("Clear all", key="btn_clear_jobs", on_click=clear_jobs)

            for index, job_id in enumerate(st.session_state.jobs, start=1):
                title_now = (st.session_state.get(f"jt_{job_id}") or "").strip()
                text_now = (st.session_state.get(f"jd_{job_id}") or "").strip()
                label = title_now or f"Job {index}"
                status = f"{len(text_now.split())} words" if text_now else "empty"
                with st.expander(f"{label} ({status})", expanded=(not text_now and len(st.session_state.jobs) <= 3)):
                    st.text_input("Job title", key=f"jt_{job_id}", placeholder="e.g. Senior Backend Engineer")
                    st.text_area(
                        "Job description",
                        key=f"jd_{job_id}",
                        height=180,
                        placeholder="Paste the full job description, including requirements and nice-to-haves.",
                    )
                    st.button("Remove this job", key=f"rm_{job_id}", on_click=remove_job, args=(job_id,))

    # ---- Collect and analyze --------------------------------------------
    jobs_list: list[tuple[str, str]] = []
    skipped = 0
    for index, job_id in enumerate(st.session_state.jobs, start=1):
        title = (st.session_state.get(f"jt_{job_id}") or "").strip() or f"Job {index}"
        text = (st.session_state.get(f"jd_{job_id}") or "").strip()
        if len(text) >= MIN_JD_CHARS:
            jobs_list.append((title, text))
        elif text:
            skipped += 1
    jobs_tuple = tuple(jobs_list)

    if skipped:
        st.warning(f"{skipped} job description(s) are too short to analyze (under {MIN_JD_CHARS} characters) and will be skipped.")

    ready = bool(resume_text) and bool(jobs_tuple)
    if st.button("Analyze match", type="primary", key="btn_analyze", disabled=not ready):
        st.session_state.snapshot = {"resume": resume_text, "jobs": jobs_tuple, "label": resume_label}
        st.toast("Analysis complete. Open the Rankings tab.")
    if not ready:
        missing = []
        if not resume_text:
            missing.append("a resume")
        if not jobs_tuple:
            missing.append("at least one job description")
        st.caption("Add " + " and ".join(missing) + " to continue.")
    elif st.session_state.snapshot is not None:
        st.caption("Results are ready in the other tabs. Select Analyze match again after changing inputs.")

# Stale-results banner
snap = st.session_state.snapshot
if snap is not None and (snap["resume"] != resume_text or snap["jobs"] != jobs_tuple):
    banner.info("Your inputs have changed since the last analysis. Select Analyze match in Setup to refresh the results.")

# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------
result: AnalysisResult | None = None
if snap is not None:
    try:
        result = run_analysis(snap["resume"], snap["jobs"], skill_pct / 100)
    except ValueError as exc:
        st.error(str(exc))

NO_RESULTS = (
    "Nothing to show yet",
    "Add your resume and at least one job description in Setup, then select Analyze match.",
)


def _job_select(label: str, key: str, titles: list[str]) -> str:
    if st.session_state.get(key) not in titles:
        st.session_state.pop(key, None)
    return st.selectbox(label, titles, key=key)


# ---- Rankings -------------------------------------------------------------
with tab_rank:
    if result is None:
        html(ui.empty_state(*NO_RESULTS))
    else:
        best = result.matches[0]
        html(
            ui.hero(
                best.title,
                best.overall * 100,
                best.text_similarity * 100,
                None if best.skill_coverage is None else best.skill_coverage * 100,
                len(best.matched),
                len(best.missing_required),
            )
        )
        st.write("")
        summary = result.summary_df()
        top_missing = result.top_missing_df(limit=1)
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(ui.kpi("Jobs analyzed", len(result.matches)), unsafe_allow_html=True)
        k2.markdown(ui.kpi("Skills in resume", len(result.resume_skills)), unsafe_allow_html=True)
        k3.markdown(
            ui.kpi("Average match", f"{summary['Overall match (%)'].mean():.0f}%", "across all jobs"),
            unsafe_allow_html=True,
        )
        if top_missing.empty:
            k4.markdown(ui.kpi("Top gap", "None", "no missing skills"), unsafe_allow_html=True)
        else:
            row = top_missing.iloc[0]
            k4.markdown(ui.kpi("Top gap", row["Skill"], f"missing in {row['Jobs missing in']} job(s)"), unsafe_allow_html=True)
        st.write("")

        show_chart(charts.ranking_bar(summary), key="chart_ranking")

        table = summary[
            ["Rank", "Job", "Overall match (%)", "Text similarity (%)", "Skill coverage (%)", "Matched skills", "Missing required"]
        ]
        show_df(
            table,
            column_config={
                "Overall match (%)": st.column_config.ProgressColumn(
                    "Overall match (%)", min_value=0, max_value=100, format="%.1f"
                ),
            },
        )
        show_chart(charts.score_breakdown(summary), key="chart_breakdown")
        st.caption(
            "Raw TF-IDF similarity between a resume and a job post is usually low even for strong fits. "
            "Compare jobs against each other; skill coverage is easier to read in absolute terms."
        )

# ---- Skill gap -------------------------------------------------------------
with tab_gap:
    if result is None:
        html(ui.empty_state(*NO_RESULTS))
    else:
        titles = [m.title for m in result.matches]
        chosen = _job_select("Job to inspect", "gap_job", titles)
        match = result.match_for(chosen)

        c1, c2 = st.columns([1, 1.6], gap="large")
        with c1:
            with st.container(border=True):
                show_chart(charts.match_gauge(match.overall * 100), key="chart_gauge")
                cov = "n/a" if match.skill_coverage is None else f"{match.skill_coverage * 100:.0f}%"
                st.caption(f"Rank {match.rank} of {len(titles)}. Text similarity {match.text_similarity * 100:.0f}%, skill coverage {cov}.")
        with c2:
            with st.container(border=True):
                st.markdown(f"**Matched skills ({len(match.matched)})**")
                html(ui.chips(match.matched, "ok") or '<p class="empty-note">No matching skills found.</p>')
                st.markdown(f"**Missing, required ({len(match.missing_required)})**")
                html(ui.chips(match.missing_required, "miss") or '<p class="empty-note">No required skills missing.</p>')
                st.markdown(f"**Missing, preferred ({len(match.missing_preferred)})**")
                html(ui.chips(match.missing_preferred, "pref") or '<p class="empty-note">No preferred skills missing.</p>')
                if not match.job_skills:
                    st.warning("No known skills were detected in this job description, so its score uses text similarity only.")

        d1, d2 = st.columns(2, gap="large")
        with d1:
            show_chart(charts.category_chart(result.category_df(match)), key="chart_category")
        with d2:
            show_chart(
                charts.skills_donut(len(match.matched), len(match.missing_required), len(match.missing_preferred)),
                key="chart_donut",
            )

        st.markdown("#### Across all jobs")
        matrix = result.skill_matrix()
        if matrix.empty:
            st.caption("No known skills were detected in any job description.")
        else:
            html(ui.gap_legend())
            show_chart(charts.gap_matrix(matrix), key="chart_matrix")
            if result.distinct_job_skills() > len(matrix):
                st.caption(f"Showing the {len(matrix)} most requested of {result.distinct_job_skills()} skills. The Export tab has all of them.")
            top = result.top_missing_df()
            if not top.empty:
                show_chart(charts.top_missing_bar(top), key="chart_topmissing")

# ---- Improve resume ---------------------------------------------------------
with tab_improve:
    if result is None:
        html(ui.empty_state(*NO_RESULTS))
    else:
        st.info(NO_INVENTION_NOTE)
        titles = [m.title for m in result.matches]
        chosen = _job_select("Suggestions for", "improve_job", titles)
        match = result.match_for(chosen)

        st.markdown(f"#### For {match.title}")
        job_tips = build_job_suggestions(match, result.resume_skills)
        if job_tips:
            html("".join(ui.tip(t.priority, t.area, t.title, t.detail) for t in job_tips))
        else:
            st.caption("No job-specific suggestions for this posting.")

        st.markdown("#### For your resume in general")
        general_tips = general_suggestions(snap["resume"])
        if general_tips:
            html("".join(ui.tip(t.priority, t.area, t.title, t.detail) for t in general_tips))
        else:
            st.caption("No structural issues detected.")

# ---- Export -----------------------------------------------------------------
with tab_export:
    if result is None:
        html(ui.empty_state(*NO_RESULTS))
    else:
        st.markdown("Download the results as CSV files to open in Excel, Google Sheets, or pandas.")
        summary = result.summary_df()
        gaps = result.gap_df()
        tips = all_suggestions_df(result, snap["resume"])

        e1, e2, e3 = st.columns(3)
        e1.download_button(
            "Download job ranking",
            data=summary.to_csv(index=False).encode("utf-8"),
            file_name="skillmap_ranking.csv",
            mime="text/csv",
            key="dl_ranking",
        )
        e2.download_button(
            "Download skill gap detail",
            data=gaps.to_csv(index=False).encode("utf-8"),
            file_name="skillmap_skill_gaps.csv",
            mime="text/csv",
            key="dl_gaps",
        )
        e3.download_button(
            "Download suggestions",
            data=tips.to_csv(index=False).encode("utf-8"),
            file_name="skillmap_suggestions.csv",
            mime="text/csv",
            key="dl_tips",
        )

        st.markdown("#### Ranking")
        show_df(summary)
        st.markdown("#### Skill gap detail")
        show_df(gaps)
        st.markdown("#### Skills found in your resume")
        show_df(result.resume_skills_df())
