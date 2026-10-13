"""Plotly figures, styled for the dark navy / indigo theme."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

# Palette (keep in sync with ui.py and .streamlit/config.toml)
BG = "#0A1020"
SURFACE = "#111A2E"
GRID = "#22304D"
TEXT = "#E7ECF7"
MUTED = "#93A0BD"
INDIGO = "#6366F1"
INDIGO_LIGHT = "#818CF8"
SKY = "#38BDF8"
GREEN = "#34D399"
AMBER = "#F59E0B"
ROSE = "#FB7185"
FONT = "Plus Jakarta Sans, Inter, system-ui, -apple-system, Segoe UI, sans-serif"


def _style(fig: go.Figure, height: int = 360, title: str | None = None) -> go.Figure:
    fig.update_layout(
        height=height,
        title=dict(text=title, x=0, font=dict(size=15, color=TEXT)) if title else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=TEXT, size=13),
        margin=dict(l=8, r=8, t=48 if title else 16, b=8),
        legend=dict(orientation="h", y=1.12, x=0, font=dict(color=MUTED)),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=GRID, font=dict(color=TEXT, family=FONT)),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=MUTED))
    return fig


def _wrap(label: str, width: int = 34) -> str:
    return label if len(label) <= width else label[: width - 1].rstrip() + "…"


def ranking_bar(summary: pd.DataFrame) -> go.Figure:
    """Horizontal bars of overall match, best job at the top."""
    df = summary.iloc[::-1]
    values = df["Overall match (%)"].tolist()
    fig = go.Figure(
        go.Bar(
            x=values,
            y=[_wrap(j) for j in df["Job"]],
            orientation="h",
            marker=dict(color=values, colorscale=[[0, "#3B3F9E"], [1, INDIGO_LIGHT]], cmin=0, cmax=max(values + [1])),
            text=[f"{v:.1f}%" for v in values],
            textposition="outside",
            textfont=dict(color=TEXT),
            customdata=df["Job"],
            hovertemplate="<b>%{customdata}</b><br>Overall match: %{x:.1f}%<extra></extra>",
        )
    )
    fig.update_xaxes(range=[0, min(100, max(values + [10]) * 1.25)], title="Overall match (%)")
    fig.update_yaxes(automargin=True)
    return _style(fig, height=max(240, 62 * len(df) + 70), title="Jobs ranked by overall match")


def score_breakdown(summary: pd.DataFrame) -> go.Figure:
    """Grouped bars: TF-IDF text similarity vs skill coverage per job."""
    jobs = [_wrap(j, 26) for j in summary["Job"]]
    fig = go.Figure()
    fig.add_bar(
        name="Text similarity (TF-IDF)",
        x=jobs,
        y=summary["Text similarity (%)"],
        marker_color=INDIGO,
        hovertemplate="%{x}<br>Text similarity: %{y:.1f}%<extra></extra>",
    )
    fig.add_bar(
        name="Skill coverage",
        x=jobs,
        y=summary["Skill coverage (%)"],
        marker_color=SKY,
        hovertemplate="%{x}<br>Skill coverage: %{y:.1f}%<extra></extra>",
    )
    fig.update_layout(barmode="group", bargap=0.28)
    fig.update_yaxes(range=[0, 100], title="Percent")
    return _style(fig, height=360, title="What drives each score")


def match_gauge(value_pct: float, title: str = "Overall match") -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value_pct,
            number=dict(suffix="%", font=dict(size=40, color=TEXT, family=FONT), valueformat=".0f"),
            title=dict(text=title, font=dict(size=14, color=MUTED)),
            gauge=dict(
                axis=dict(range=[0, 100], tickcolor=GRID, tickfont=dict(color=MUTED)),
                bar=dict(color=INDIGO_LIGHT, thickness=0.28),
                bgcolor="#16223B",
                borderwidth=0,
            ),
        )
    )
    fig.update_layout(height=250, margin=dict(l=24, r=24, t=48, b=8), paper_bgcolor="rgba(0,0,0,0)", font=dict(family=FONT))
    return fig


def category_chart(cat_df: pd.DataFrame) -> go.Figure:
    """Radar of per-category coverage; falls back to bars with fewer than 3 axes."""
    if cat_df.empty:
        return _style(go.Figure(), height=320, title="Coverage by skill area")
    cats = cat_df["Category"].tolist()
    vals = cat_df["Coverage (%)"].tolist()
    hover = [f"{c}: {v:.0f}% ({h} of {n})" for c, v, h, n in zip(cats, vals, cat_df["You have"], cat_df["Job asks for"])]
    if len(cats) < 3:
        fig = go.Figure(go.Bar(x=cats, y=vals, marker_color=INDIGO, text=[f"{v:.0f}%" for v in vals], textposition="outside"))
        fig.update_yaxes(range=[0, 110], title="Coverage (%)")
        return _style(fig, height=320, title="Coverage by skill area")
    fig = go.Figure(
        go.Scatterpolar(
            r=vals + vals[:1],
            theta=cats + cats[:1],
            fill="toself",
            fillcolor="rgba(99,102,241,0.30)",
            line=dict(color=INDIGO_LIGHT, width=2),
            hovertext=hover + hover[:1],
            hoverinfo="text",
        )
    )
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(range=[0, 100], gridcolor=GRID, linecolor=GRID, tickfont=dict(color=MUTED, size=10), ticksuffix="%"),
            angularaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(color=TEXT, size=12)),
        ),
        showlegend=False,
    )
    return _style(fig, height=360, title="Coverage by skill area")


def skills_donut(matched: int, missing_required: int, missing_preferred: int) -> go.Figure:
    total = matched + missing_required + missing_preferred
    fig = go.Figure(
        go.Pie(
            labels=["Matched", "Missing (required)", "Missing (preferred)"],
            values=[matched, missing_required, missing_preferred],
            hole=0.66,
            marker=dict(colors=[GREEN, ROSE, AMBER], line=dict(color=BG, width=3)),
            textinfo="value",
            sort=False,
            hovertemplate="%{label}: %{value}<extra></extra>",
        )
    )
    fig.add_annotation(
        text=f"<b>{matched}</b> of {total}<br><span style='font-size:12px;color:{MUTED}'>skills matched</span>",
        showarrow=False,
        font=dict(size=20, color=TEXT),
    )
    _style(fig, height=320, title="Skills this job asks for")
    fig.update_layout(legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center", font=dict(color=MUTED)))
    return fig


def gap_matrix(matrix: pd.DataFrame) -> go.Figure:
    """Heatmap of skills x jobs: matched / missing required / missing preferred."""
    labels = {0: "Not requested", 1: "Missing (preferred)", 2: "Missing (required)", 3: "Matched"}
    hover = [[labels[int(v)] for v in row] for row in matrix.to_numpy()]
    colors = ["#111A2E", AMBER, ROSE, GREEN]
    colorscale = []
    for i, color in enumerate(colors):
        colorscale += [[i / 4, color], [(i + 1) / 4, color]]
    fig = go.Figure(
        go.Heatmap(
            z=matrix.to_numpy(),
            x=[_wrap(c, 22) for c in matrix.columns],
            y=matrix.index.tolist(),
            zmin=-0.5,
            zmax=3.5,
            colorscale=colorscale,
            showscale=False,
            xgap=3,
            ygap=3,
            text=hover,
            hovertemplate="<b>%{y}</b><br>%{x}<br>%{text}<extra></extra>",
        )
    )
    fig.update_yaxes(autorange="reversed", automargin=True)
    fig.update_xaxes(side="top", tickangle=0)
    return _style(fig, height=max(260, 24 * len(matrix) + 120), title=None)


def top_missing_bar(top: pd.DataFrame) -> go.Figure:
    df = top.iloc[::-1]
    fig = go.Figure(
        go.Bar(
            x=df["Jobs missing in"],
            y=df["Skill"],
            orientation="h",
            marker_color=ROSE,
            text=df["Jobs missing in"],
            textposition="outside",
            textfont=dict(color=TEXT),
            customdata=df[["Required in jobs"]],
            hovertemplate="<b>%{y}</b><br>Missing in %{x} job(s)<br>Required in %{customdata[0]}<extra></extra>",
        )
    )
    fig.update_xaxes(title="Jobs where this skill is missing", dtick=1, rangemode="tozero")
    fig.update_yaxes(automargin=True)
    return _style(fig, height=max(240, 30 * len(df) + 90), title="Most common missing skills")
