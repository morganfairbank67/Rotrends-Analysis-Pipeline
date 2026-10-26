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

ui.page_header(
    "Title keywords",
    "What are popular games called, and which name patterns have players to spare?",
)
ui.require_games(games)

controls = st.columns([2, 2, 3])
length = controls[0].selectbox("Look at", list(LENGTHS))
min_games = controls[1].slider("Phrase must appear in at least", 2, 10, 2, help="Number of games")

table = phrase_table(games, LENGTHS[length], min_games)
if table.empty:
    st.info("No phrase appears in that many games. Lower the slider or widen the sidebar filters.")
    st.stop()

open_phrases = table[table["verdict"] == "Underserved"]
if open_phrases.empty:
    ui.takeaway("No phrase clearly stands out as under-served with the current filters.")
else:
    pick = open_phrases.iloc[0]
    ui.takeaway(
        f"**\"{pick['phrase']}\"** is used by {int(pick['games'])} games that together hold "
        f"{int(pick['total_ccu']):,} players, {ui.times(pick['demand_index'])} the share you would "
        "expect for that many games."
    )

common_tab, gap_tab, inside_tab, tricks_tab = st.tabs(
    ["Most common", "Best opportunities", "Look inside a phrase", "Title tricks"]
)

with common_tab:
    ui.section("Most used phrases", "How many games have each phrase in their name.")
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
    ui.section(
        "Phrases with the most players for their number of games",
        "1x is a fair share. Orange means one huge game is doing most of the work.",
    )
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
    ui.how_to_read(
        "A phrase's **fair share** is its share of games. If 2% of games use a phrase, a fair "
        "share is 2% of players. **Underserved** means well above that and the typical game "
        "using it does well. **Hit-driven** means mostly one big game. Phrases that appear "
        "in exactly the same games are merged, keeping the longest.\n\n"
        "Only games in the Rotrends top lists are counted."
    )
    with st.expander("Advanced: supply against demand"):
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
        st.caption("Top-left means many players and few games. Both axes are logarithmic.")

with inside_tab:
    ui.section("Look inside a phrase", "Pick a phrase to see every game that uses it.")
    choice = st.selectbox("Phrase", table["phrase"])
    matches = phrase_games(games, choice)
    row = table[table["phrase"] == choice].iloc[0]
    stats = st.columns(3)
    stats[0].metric("Games", int(row["games"]))
    stats[1].metric("Players online", ui.compact(row["total_ccu"]))
    stats[2].metric("Biggest game's share", f"{row['top_game_share']:.0%}")
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
    ui.section(
        "Do emoji and tags in the title go with more players?",
        "Typical (median) players online, with and without each trick.",
    )
    impact = title_feature_impact(games)
    impact["present"] = impact["present"].map({True: "Has it", False: "Does not"})
    fig = px.bar(
        impact,
        x="feature",
        y="median_ccu",
        color="present",
        barmode="group",
        text=impact["median_ccu"].map(ui.compact),
        color_discrete_sequence=[charts.SERIES[0], "#8a8984"],
        hover_data={"games": True},
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(title=None)
    fig.update_yaxes(title="Typical players online")
    charts.show(fig, 420)
    st.caption(
        "This shows a link, not a cause. Established hits tend to carry update tags and emoji "
        "because they are updated often."
    )
