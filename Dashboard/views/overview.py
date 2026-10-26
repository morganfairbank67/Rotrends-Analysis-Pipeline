import plotly.express as px
import streamlit as st

from Analytics.market import segment_table
from Dashboard import charts
from Dashboard.data import current_games

games = current_games()

st.title("Roblox market overview")
st.caption(
    "Snapshot of the top games tracked on Rotrends. A game that appears in several top lists "
    "is counted once."
)

if games.empty:
    st.warning("No games match the current filters.")
    st.stop()

recent = (games["age_days"] <= 90).mean()
cols = st.columns(5)
cols[0].metric("Games", f"{len(games):,}")
cols[1].metric("Total CCU", f"{games['players_ccu'].sum():,}")
cols[2].metric("Median CCU", f"{games['players_ccu'].median():,.0f}")
cols[3].metric("Median age", f"{games['age_days'].median() / 365:.1f} yrs")
cols[4].metric("Under 90 days old", f"{recent:.0%}")

genres = segment_table(games, "genre")
left, right = st.columns(2)

with left:
    share = genres.melt(
        id_vars="genre",
        value_vars=["ccu_share", "game_share"],
        var_name="measure",
        value_name="share",
    )
    share["measure"] = share["measure"].map(
        {"ccu_share": "Share of players", "game_share": "Share of games"}
    )
    order = genres.sort_values("ccu_share")["genre"]
    fig = px.bar(
        share,
        x="share",
        y="genre",
        color="measure",
        barmode="group",
        orientation="h",
        color_discrete_sequence=charts.SERIES[:2],
        category_orders={"genre": order.tolist()},
        title="Players vs games by genre",
    )
    fig.update_xaxes(tickformat=".0%", title=None)
    fig.update_yaxes(title=None)
    fig.update_traces(hovertemplate="%{y}: %{x:.1%}<extra>%{fullData.name}</extra>")
    st.plotly_chart(charts.style(fig, 480), width="stretch")

with right:
    tree = games.groupby(["genre", "sub_genre"], as_index=False)["players_ccu"].sum()
    fig = px.treemap(
        tree,
        path=["genre", "sub_genre"],
        values="players_ccu",
        color="players_ccu",
        color_continuous_scale=charts.BLUE_SCALE,
        title="Where the players are",
    )
    fig.update_traces(hovertemplate="%{label}<br>%{value:,} players<extra></extra>")
    fig.update_coloraxes(showscale=False)
    st.plotly_chart(charts.style(fig, 480), width="stretch")

st.subheader("Biggest games right now")
top = games.nlargest(15, "players_ccu")[
    ["game_name", "genre", "sub_genre", "players_ccu", "avg_session", "like_ratio", "age_days"]
]
st.dataframe(
    top,
    hide_index=True,
    width="stretch",
    column_config={
        "game_name": "Game",
        "genre": "Genre",
        "sub_genre": "Sub-genre",
        "players_ccu": st.column_config.NumberColumn("Players now", format="%d"),
        "avg_session": st.column_config.NumberColumn("Avg session (min)", format="%.1f"),
        "like_ratio": st.column_config.ProgressColumn("Like ratio", min_value=0, max_value=1),
        "age_days": st.column_config.NumberColumn("Age (days)", format="%d"),
    },
)
