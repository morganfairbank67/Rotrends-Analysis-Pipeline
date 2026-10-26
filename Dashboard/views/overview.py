import plotly.express as px
import streamlit as st

from Analytics.market import segment_table
from Dashboard import charts, ui
from Dashboard.data import current_games

games = current_games()

ui.page_header("Market overview", "Where are the players, and how many games share them?")
ui.require_games(games)

recent = (games["age_days"] <= 90).mean()
cols = st.columns(4)
cols[0].metric("Games", f"{len(games):,}")
cols[1].metric("Players online", ui.compact(games["players_ccu"].sum()))
cols[2].metric("Typical game has", f"{games['players_ccu'].median():,.0f} players")
cols[3].metric("Released in last 90 days", f"{recent:.0%}")

genres = segment_table(games, "genre")
genres["gap"] = (genres["ccu_share"] - genres["game_share"]) * 100
genres = genres.sort_values("gap")

ui.section(
    "Which genres hold more players than their number of games?",
    "Share of players minus share of games, in percentage points.",
)
leader = genres.iloc[-1]
trailer = genres.iloc[0]
ui.takeaway(
    f"**{leader['genre']}** holds {leader['gap']:.0f} points more of the audience than its share "
    f"of games. **{trailer['genre']}** is the reverse, with {abs(trailer['gap']):.0f} points "
    "fewer players than its game count would suggest."
)
genres["side"] = genres["gap"].map(lambda v: "More players than games" if v >= 0 else
                                   "More games than players")
fig = px.bar(
    genres,
    x="gap",
    y="genre",
    color="side",
    orientation="h",
    text=genres["gap"].map(lambda v: f"{v:+.1f}"),
    color_discrete_map={"More players than games": charts.SERIES[0],
                        "More games than players": "#8a8984"},
    hover_data={"games": True, "total_ccu": ":,", "gap": False, "side": False},
)
fig.update_traces(textposition="outside", cliponaxis=False)
fig.update_xaxes(title="Percentage points (right = under-served)", zeroline=True)
fig.update_yaxes(title=None)
charts.show(fig, max(360, 34 * len(genres) + 100))

ui.section(
    "Where do the players actually play?",
    "Box size is players online. Click a genre to zoom.",
)
tree = games.groupby(["genre", "sub_genre"], as_index=False)["players_ccu"].sum()
fig = px.treemap(
    tree,
    path=["genre", "sub_genre"],
    values="players_ccu",
    color="genre",
    color_discrete_sequence=charts.SERIES,
)
fig.update_traces(hovertemplate="%{label}<br>%{value:,} players<extra></extra>",
                  textinfo="label+percent root")
charts.show(fig, 520)

ui.section("Biggest games right now", "The 15 games with the most players online.")
top = games.nlargest(15, "players_ccu")[
    ["display_name", "genre", "sub_genre", "players_ccu", "avg_session", "like_ratio", "age_days"]
]
st.dataframe(
    top,
    hide_index=True,
    width="stretch",
    column_config={
        "display_name": "Game",
        "genre": "Genre",
        "sub_genre": "Sub-genre",
        "players_ccu": st.column_config.NumberColumn("Players now", format="%d"),
        "avg_session": st.column_config.NumberColumn("Avg session (min)", format="%.1f"),
        "like_ratio": st.column_config.ProgressColumn("Liked", min_value=0, max_value=1,
                                                      format="percent"),
        "age_days": st.column_config.NumberColumn("Age (days)", format="%d"),
    },
)
