import plotly.express as px
import streamlit as st

from Analytics.market import segment_table
from Analytics.summary import headline_findings
from Dashboard import charts, ui
from Dashboard.data import current_games, current_history

games = current_games()
history = current_history()

ui.require_games(games)

latest = games["extract_date"].max().strftime("%d %b %Y")
ui.page_header(
    "Roblox market analysis",
    f"Snapshot {latest}  |  {len(games):,} games  |  {ui.compact(games['players_ccu'].sum())} "
    "concurrent players",
)

findings = headline_findings(games)
if findings:
    for column, finding in zip(st.columns(len(findings)), findings, strict=True):
        with column.container(border=True, height=185):
            st.caption(finding.label)
            st.markdown(f"**{finding.headline}**")
            st.caption(finding.detail)

genres = segment_table(games, "genre")
genres = genres[genres["genre"] != "Unknown"]
genres["gap"] = (genres["ccu_share"] - genres["game_share"]) * 100
genres = genres.sort_values("gap")

ui.section("Player share minus game share, by genre", "Percentage points")
genres["side"] = genres["gap"].map(
    lambda v: "More players than games" if v >= 0 else "More games than players"
)
fig = px.bar(
    genres,
    x="gap",
    y="genre",
    color="side",
    orientation="h",
    text=genres["gap"].map(lambda v: f"{v:+.1f}"),
    color_discrete_map={
        "More players than games": charts.SERIES[0],
        "More games than players": charts.MUTED,
    },
    hover_data={"games": True, "total_ccu": ":,", "gap": False, "side": False},
)
fig.update_traces(textposition="outside", cliponaxis=False)
fig.update_xaxes(title=None)
fig.update_yaxes(title=None)
charts.show(fig, max(340, 32 * len(genres) + 90))

ui.section("Concurrent players by genre and sub-genre")
tree = games.groupby(["genre", "sub_genre"], as_index=False)["players_ccu"].sum()
fig = px.treemap(
    tree,
    path=["genre", "sub_genre"],
    values="players_ccu",
    color="genre",
    color_discrete_sequence=charts.SERIES,
)
fig.update_traces(
    hovertemplate="%{label}<br>%{value:,} players<extra></extra>", textinfo="label+percent root"
)
charts.show(fig, 500)

ui.section("Largest games")
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
        "players_ccu": st.column_config.NumberColumn("Players", format="%d"),
        "avg_session": st.column_config.NumberColumn("Avg session (min)", format="%.1f"),
        "like_ratio": st.column_config.ProgressColumn(
            "Liked", min_value=0, max_value=1, format="percent"
        ),
        "age_days": st.column_config.NumberColumn("Age (days)", format="%d"),
    },
)
