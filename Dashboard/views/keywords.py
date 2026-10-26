import plotly.express as px
import streamlit as st

from Analytics.insights import title_feature_impact
from Analytics.text import phrase_games, phrase_table
from Dashboard import charts, ui
from Dashboard.data import current_games

LENGTHS = {
    "Any length": (1, 2, 3),
    "Single words": (1,),
    "Two-word phrases": (2,),
    "Three-word phrases": (3,),
}

games = current_games()

ui.page_header("Title keywords", "Phrase frequency and demand relative to supply")
ui.require_games(games)

controls = st.columns([2, 2, 3])
length = controls[0].selectbox("Phrase type", list(LENGTHS))
min_games = controls[1].slider("Minimum games", 2, 10, 2)

table = phrase_table(games, LENGTHS[length], min_games)
if table.empty:
    st.info("No phrase meets the minimum. Lower it or widen the filters.")
    st.stop()

common_tab, gap_tab, inside_tab, tricks_tab = st.tabs(
    ["Frequency", "Opportunities", "Phrase detail", "Title features"]
)

with common_tab:
    ui.section("Most used phrases", "Games using each phrase")
    common = table.nlargest(15, "games").sort_values("games")
    fig = px.bar(
        common,
        x="games",
        y="phrase",
        orientation="h",
        text="games",
        color_discrete_sequence=[charts.SERIES[0]],
        hover_data={"total_ccu": ":,", "top_game": True, "games": False},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(title="Games using the phrase")
    fig.update_yaxes(title=None)
    charts.show(fig, 480)

with gap_tab:
    ui.section("Share of players relative to share of games", "1x is a proportional share.")
    best = table.nlargest(15, "opportunity_score").sort_values("opportunity_score")
    fig = px.bar(
        best,
        x="demand_index",
        y="phrase",
        color="verdict",
        orientation="h",
        text=best["demand_index"].map(ui.times),
        color_discrete_map=charts.VERDICT_COLORS,
        category_orders={"verdict": charts.VERDICT_ORDER},
        hover_data={"games": True, "total_ccu": ":,", "top_game": True, "demand_index": False,
                    "verdict": False},
    )
    fig.add_vline(x=1, line_dash="dot", line_color="rgba(128,128,128,0.8)")
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(title="Times its fair share of players")
    fig.update_yaxes(title=None)
    charts.show(fig, 520)
    with st.expander("Supply and demand"):
        fig = px.scatter(
            table,
            x="games",
            y="total_ccu",
            color="verdict",
            size="median_ccu",
            size_max=34,
            log_x=True,
            log_y=True,
            hover_name="phrase",
            hover_data={"top_game": True, "demand_index": ":.2f", "verdict": False},
            color_discrete_map=charts.VERDICT_COLORS,
            category_orders={"verdict": charts.VERDICT_ORDER},
        )
        fig.update_xaxes(title="Games using the phrase")
        fig.update_yaxes(title="Total players online")
        charts.show(fig, 480)

with inside_tab:
    choice = st.selectbox("Phrase", table["phrase"])
    matches = phrase_games(games, choice)
    row = table[table["phrase"] == choice].iloc[0]
    stats = st.columns(3)
    stats[0].metric("Games", int(row["games"]))
    stats[1].metric("Players", ui.compact(row["total_ccu"]))
    stats[2].metric("Largest game share", f"{row['top_game_share']:.0%}")
    st.dataframe(
        matches[["display_name", "genre", "sub_genre", "players_ccu", "avg_session", "like_ratio",
                 "age_days"]],
        hide_index=True,
        width="stretch",
        column_config={
            "display_name": "Game", "genre": "Genre", "sub_genre": "Sub-genre",
            "players_ccu": st.column_config.NumberColumn("Players now", format="%d"),
            "avg_session": st.column_config.NumberColumn("Avg session (min)", format="%.1f"),
            "like_ratio": st.column_config.ProgressColumn("Liked", min_value=0, max_value=1,
                                                          format="percent"),
            "age_days": st.column_config.NumberColumn("Age (days)", format="%d"),
        },
    )

with tricks_tab:
    ui.section("Median players by title feature")
    impact = title_feature_impact(games)
    impact["present"] = impact["present"].map({True: "Has it", False: "Does not"})
    fig = px.bar(
        impact,
        x="feature",
        y="median_ccu",
        color="present",
        barmode="group",
        text=impact["median_ccu"].map(ui.compact),
        color_discrete_sequence=[charts.SERIES[0], charts.MUTED],
        hover_data={"games": True},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(title=None)
    fig.update_yaxes(title="Median players")
    charts.show(fig, 420)
