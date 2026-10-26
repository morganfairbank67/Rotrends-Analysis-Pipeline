import plotly.express as px
import streamlit as st

from Analytics.insights import age_cohorts
from Analytics.market import genre_matrix, segment_table
from Dashboard import charts, ui
from Dashboard.data import current_games

games = current_games()

ui.page_header("Market gaps", "Demand relative to supply by genre and sub-genre")
ui.require_games(games)

controls = st.columns([2, 2, 3])
level = controls[0].radio("Group by", ["Genre", "Sub-genre"], horizontal=True)
column = "genre" if level == "Genre" else "sub_genre"
min_games = controls[1].slider("Minimum games per group", 1, 15, 3)

table = segment_table(games, column, min_games=min_games)
table = table[~table[column].isin(["Unknown", "Unclassified"])]
if table.empty:
    st.info("No group has that many games. Lower the slider or widen the sidebar filters.")
    st.stop()

ranking_tab, newcomer_tab, heatmap_tab, age_tab = st.tabs(
    ["Ranking", "Entry", "Genre map", "Release age"]
)

with ranking_tab:
    ui.section("Share of players relative to share of games", "1x is a proportional share.")
    ranked = table.sort_values("demand_index")
    fig = px.bar(
        ranked,
        x="demand_index",
        y=column,
        color="verdict",
        orientation="h",
        text=ranked["demand_index"].map(ui.times),
        color_discrete_map=charts.VERDICT_COLORS,
        category_orders={"verdict": charts.VERDICT_ORDER},
        hover_data={"games": True, "total_ccu": ":,", "demand_index": False, "verdict": False},
    )
    fig.add_vline(x=1, line_dash="dot", line_color="rgba(128,128,128,0.8)")
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(title="Times its fair share of players")
    fig.update_yaxes(title=None)
    charts.show(fig, max(380, 30 * len(ranked) + 110))

with newcomer_tab:
    ui.section("Release recency and incumbent concentration")
    fig = px.scatter(
        table,
        x="recent_share",
        y="top_game_share",
        size="games",
        size_max=44,
        color="verdict",
        hover_name=column,
        hover_data={"games": True, "top_game": True, "verdict": False,
                    "recent_share": ":.0%", "top_game_share": ":.0%"},
        color_discrete_map=charts.VERDICT_COLORS,
        category_orders={"verdict": charts.VERDICT_ORDER},
    )
    for row in table.nlargest(6, "total_ccu").itertuples():
        fig.add_annotation(x=row.recent_share, y=row.top_game_share, text=getattr(row, column),
                           showarrow=False, yshift=16, font_size=12)
    fig.add_annotation(xref="paper", yref="paper", x=0.99, y=0.02, text="Open",
                       showarrow=False, font=dict(size=13, color=charts.SERIES[0]), xanchor="right")
    fig.add_annotation(xref="paper", yref="paper", x=0.01, y=0.98, text="Concentrated",
                       showarrow=False, font=dict(size=13, color=charts.MUTED), xanchor="left",
                       yanchor="top")
    fig.update_xaxes(title="Share of games under 90 days old", tickformat=".0%")
    fig.update_yaxes(title="Largest game's share of group players", tickformat=".0%")
    charts.show(fig, 520)

with heatmap_tab:
    measure = st.radio("Measure", ["Players", "Games"], horizontal=True)
    if measure == "Players":
        matrix = genre_matrix(games, "players_ccu", "sum")
    else:
        matrix = genre_matrix(games, "game_name", "count")
    fig = px.imshow(
        matrix,
        aspect="auto",
        color_continuous_scale=charts.BLUE_SCALE,
        labels=dict(color=measure),
    )
    fig.update_xaxes(title=None, tickangle=-45)
    fig.update_yaxes(title=None)
    charts.show(fig, 560)

with age_tab:
    ui.section("Share of players and games by release age")
    cohorts = age_cohorts(games).melt(
        id_vars="age_bucket",
        value_vars=["ccu_share", "game_share"],
        var_name="measure",
        value_name="share",
    )
    cohorts["measure"] = cohorts["measure"].map(
        {"ccu_share": "Share of players", "game_share": "Share of games"}
    )
    fig = px.bar(
        cohorts,
        x="age_bucket",
        y="share",
        color="measure",
        barmode="group",
        text=cohorts["share"].map(lambda v: f"{v:.0%}"),
        color_discrete_sequence=charts.SERIES[:2],
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(title="Time since release")
    fig.update_yaxes(title=None, tickformat=".0%")
    charts.show(fig, 420)

    fresh = games[games["age_days"] <= 30].nlargest(10, "players_ccu")
    st.markdown("**Largest releases in the last 30 days**")
    st.dataframe(
        fresh[["display_name", "genre", "sub_genre", "players_ccu", "age_days"]],
        hide_index=True,
        width="stretch",
        column_config={
            "display_name": "Game", "genre": "Genre", "sub_genre": "Sub-genre",
            "players_ccu": st.column_config.NumberColumn("Players now", format="%d"),
            "age_days": st.column_config.NumberColumn("Age (days)", format="%d"),
        },
    )

with st.expander("Data"):
    st.dataframe(
        table[[column, "verdict", "games", "total_ccu", "median_ccu", "demand_index",
               "opportunity_score", "top_game"]],
        hide_index=True,
        width="stretch",
        column_config={
            column: level, "verdict": "Verdict", "games": "Games",
            "total_ccu": st.column_config.NumberColumn("Total players", format="%d"),
            "median_ccu": st.column_config.NumberColumn("Typical game", format="%d"),
            "demand_index": st.column_config.NumberColumn("Fair-share multiple", format="%.2f"),
            "opportunity_score": st.column_config.NumberColumn("Opportunity", format="%.2f"),
            "top_game": "Biggest game",
        },
    )
