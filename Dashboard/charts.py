import plotly.graph_objects as go

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
BLUE_SCALE = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
VERDICT_COLORS = {
    "Underserved": "#2a78d6",
    "Hit-driven": "#eb6834",
    "Balanced": "#1baf7a",
    "Crowded": "#8a8984",
}
VERDICT_ORDER = list(VERDICT_COLORS)
GRID = "rgba(128,128,128,0.2)"


def style(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=40, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(font_size=13),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig
