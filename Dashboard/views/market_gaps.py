import plotly.express as px
import streamlit as st

from Analytics.insights import age_cohorts
from Analytics.market import genre_matrix, segment_table
from Dashboard import charts
from Dashboard.data import current_games

games = current_games()

st.title("Market gaps")
st.caption("Where player demand is high relative to the number of games serving it.")

if games.empty:
    st.warning("No games match the current filters.")
    st.stop()

controls = st.columns([2, 2, 3])
level = controls[0].radio("Segment by", ["Genre", "Sub-genre"], horizontal=True)
column = "genre" if level == "Genre" else "sub_genre"
min_games = controls[1].slider("Minimum games", 1, 15, 3)

table = segment_table(games, column, min_games=min_games)
if table.empty:
    st.info("No segment has that many games. Lower the minimum or loosen the filters.")
    st.stop()

st.subheader("Opportunity ranking")
ranked = table.sort_values("opportunity_score")
fig = px.bar(
    ranked,
    x="opportunity_score",
    y=column,
    color="verdict",
    orientation="h",
    color_discrete_map=charts.VERDICT_COLORS,
    category_orders={"verdict": charts.VERDICT_ORDER},
    hover_data={"games": True, "total_ccu": ":,", "demand_index": ":.2f", "verdict": False},
)
fig.update_xaxes(title="Opportunity score")
fig.update_yaxes(title=None)
st.plotly_chart(charts.style(fig, max(380, 26 * len(ranked) + 80)), width="stretch")

st.subheader("Players per game")
fig = px.scatter(
    table,
    x="games",
    y="mean_ccu",
    size="total_ccu",
    size_max=48,
    color="verdict",
    hover_name=column,
    hover_data={"total_ccu": ":,", "median_ccu": ":,.0f", "top_game": True, "verdict": False},
    color_discrete_map=charts.VERDICT_COLORS,
    category_orders={"verdict": charts.VERDICT_ORDER},
    log_y=True,
)
for row in table.nlargest(6, "total_ccu").itertuples():
    fig.add_annotation(
        x=row.games, y=row.mean_ccu, text=getattr(row, column), showarrow=False, yshift=18,
        font_size=11,
    )
fig.update_xaxes(title="Games in the top lists (supply)")
fig.update_yaxes(title="Average CCU per game")
st.plotly_chart(charts.style(fig, 520), width="stretch")
st.caption(
    "Bubble size is total players. High and to the left means few games sharing many players."
)

st.subheader("Can newcomers break in?")
entry = table.copy()
entry["incumbent_dominance"] = entry["top_game_share"]
fig = px.scatter(
    entry,
    x="recent_share",
    y="incumbent_dominance",
    size="games",
    color="verdict",
    hover_name=column,
    hover_data={"games": True, "verdict": False},
    color_discrete_map=charts.VERDICT_COLORS,
    category_orders={"verdict": charts.VERDICT_ORDER},
)
fig.update_xaxes(title="Share of games under 90 days old", tickformat=".0%")
fig.update_yaxes(title="Biggest game's share of the segment's players", tickformat=".0%")
st.plotly_chart(charts.style(fig, 460), width="stretch")
st.caption(
    "Right and low is open: many fresh games and no single title hoarding the audience. "
    "Left and high means an old giant owns the segment."
)

st.subheader("Players by genre and sub-genre")
measure = st.radio("Measure", ["Total CCU", "Number of games"], horizontal=True)
if measure == "Total CCU":
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
st.plotly_chart(charts.style(fig, 520), width="stretch")

st.subheader("Do new games reach the top lists?")
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
    color_discrete_sequence=charts.SERIES[:2],
)
fig.update_xaxes(title="Time since release")
fig.update_yaxes(title=None, tickformat=".0%")
st.plotly_chart(charts.style(fig, 380), width="stretch")

fresh = games[games["age_days"] <= 30].nlargest(10, "players_ccu")
st.markdown("**Biggest games released in the last 30 days**")
st.dataframe(
    fresh[["game_name", "genre", "sub_genre", "players_ccu", "age_days", "like_ratio"]],
    hide_index=True,
    width="stretch",
)
