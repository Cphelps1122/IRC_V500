from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.theme import current_theme


def base_layout(fig, height=360):
    t = current_theme()
    fig.update_layout(
        template=t["plotly_template"],
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text"]),
        margin=dict(l=18, r=18, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor="rgba(148,163,184,0.14)", zerolinecolor="rgba(148,163,184,0.18)")
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.14)", zerolinecolor="rgba(148,163,184,0.18)")
    return fig


def line_chart(df: pd.DataFrame, x: str, y: str | list[str], title="", height=360, markers=True):
    if df.empty:
        return go.Figure()
    fig = px.line(df, x=x, y=y, markers=markers, title=title)
    return base_layout(fig, height)


def bar_chart(df: pd.DataFrame, x: str, y: str, color: str | None = None, title="", height=360, orientation="v"):
    if df.empty:
        return go.Figure()
    fig = px.bar(df, x=x, y=y, color=color, title=title, orientation=orientation)
    return base_layout(fig, height)


def state_choropleth(df: pd.DataFrame, location_col="State", value_col="Total Cost", title="State utility cost"):
    if df.empty:
        return go.Figure()
    fig = px.choropleth(
        df,
        locations=location_col,
        locationmode="USA-states",
        color=value_col,
        scope="usa",
        hover_name=location_col,
        hover_data=df.columns,
        title=title,
    )
    return base_layout(fig, 520)
