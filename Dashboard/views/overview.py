import altair as alt
import streamlit as st

from Analytics.market import segment_table
from Analytics.summary import headline_findings
from Dashboard import charts, ui, viz
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
side_scale = alt.Scale(
    domain=["More players than games", "More games than players"],
    range=[charts.SERIES[0], charts.MUTED],
)
viz.show(
    viz.hbar(
        genres,
        "genre",
        "gap",
        color="side",
        scale=side_scale,
        label=lambda v: f"{v:+.1f}",
        x_title="Percentage points",
        rule=0,
        tooltip=[
            alt.Tooltip("genre:N", title="Genre"),
            alt.Tooltip("gap:Q", title="Share gap (pts)", format="+.1f"),
            alt.Tooltip("games:Q", title="Games"),
            alt.Tooltip("total_ccu:Q", title="Players", format=","),
        ],
    )
)

ui.section("Largest sub-genres by concurrent players")
subs = (
    games[games["sub_genre"] != "Unclassified"]
    .groupby("sub_genre")
    .agg(
        players=("players_ccu", "sum"),
        games=("game_key", "nunique"),
        genre=("genre", lambda s: s.value_counts().index[0]),
    )
    .reset_index()
    .nlargest(15, "players")
)
viz.show(
    viz.hbar(
        subs,
        "sub_genre",
        "players",
        color="genre",
        label=ui.compact,
        x_format="~s",
        tooltip=[
            alt.Tooltip("sub_genre:N", title="Sub-genre"),
            alt.Tooltip("genre:N", title="Genre"),
            alt.Tooltip("players:Q", title="Players", format=","),
            alt.Tooltip("games:Q", title="Games"),
        ],
    )
)

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
