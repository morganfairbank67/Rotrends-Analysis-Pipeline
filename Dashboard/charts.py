import plotly.graph_objects as go
import streamlit as st

LIGHT = {
    "series": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6",
               "#e34948"],
    "blue": ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"],
    "verdict": {
        "Underserved": "#2a78d6",
        "Hit-driven": "#eb6834",
        "Balanced": "#1baf7a",
        "Crowded": "#8a8984",
    },
    "muted": "#8a8984",
    "text": "#14181f",
    "grid": "rgba(20,24,31,0.10)",
}
DARK = {
    "series": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#2ca02c", "#9085e9",
               "#e66767"],
    "blue": ["#14233a", "#184f95", "#2a78d6", "#6da7ec", "#cde2fb"],
    "verdict": {
        "Underserved": "#3987e5",
        "Hit-driven": "#d95926",
        "Balanced": "#199e70",
        "Crowded": "#77766f",
    },
    "muted": "#77766f",
    "text": "#e8eaee",
    "grid": "rgba(232,234,238,0.10)",
}
VERDICT_ORDER = ["Underserved", "Hit-driven", "Balanced", "Crowded"]
CONFIG = {"displayModeBar": False}

NAMES = {
    "SERIES": "series",
    "BLUE_SCALE": "blue",
    "VERDICT_COLORS": "verdict",
    "MUTED": "muted",
    "GRID": "grid",
}


def palette() -> dict:
    try:
        return DARK if st.context.theme.type == "dark" else LIGHT
    except Exception:
        return LIGHT


def __getattr__(name: str):
    if name in NAMES:
        return palette()[NAMES[name]]
    raise AttributeError(name)


def style(fig: go.Figure, height: int = 420) -> go.Figure:
    pal = palette()
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=44, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13, color=pal["text"]),
        title=dict(font=dict(size=17), x=0, xanchor="left"),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, title_text=""
        ),
        hoverlabel=dict(font_size=13),
    )
    fig.update_xaxes(gridcolor=pal["grid"], zerolinecolor=pal["grid"], linecolor=pal["grid"])
    fig.update_yaxes(gridcolor=pal["grid"], zerolinecolor=pal["grid"], linecolor=pal["grid"])
    return fig


def show(fig: go.Figure, height: int = 420) -> None:
    st.plotly_chart(style(fig, height), width="stretch", config=CONFIG)
