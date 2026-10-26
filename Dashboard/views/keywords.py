import plotly.express as px
import streamlit as st

from Analytics.insights import title_feature_impact
from Analytics.text import phrase_games, phrase_table
from Dashboard import charts
from Dashboard.data import current_games

games = current_games()

st.title("Title keywords")
st.caption("Which words and phrases games build their names around, and who is playing them.")

if games.empty:
    st.warning("No games match the current filters.")
    st.stop()

controls = st.columns([2, 2, 3])
sizes = controls[0].multiselect("Phrase length (words)", [1, 2, 3], default=[1, 2, 3])
min_games = controls[1].slider("Minimum games using phrase", 2, 10, 2)
hide_single = controls[2].toggle("Hide phrases that only repeat one game's name", value=True)

if not sizes:
    st.info("Pick at least one phrase length.")
    st.stop()

table = phrase_table(games, tuple(sizes), min_games)
if hide_single:
    table = table[table["games"] >= 2]

if table.empty:
    st.info("No phrase appears in enough games. Lower the minimum or loosen the filters.")
    st.stop()

with st.expander("How to read the scores"):
    st.markdown(
        "- **Demand index**: a phrase's share of all players divided by its share of all games. "
        "Above 1 means it holds more players than its number of games would suggest.\n"
        "- **Typical index**: the median game using the phrase compared with the median game "
        "overall. Stops one giant hit from making a whole phrase look like a gap.\n"
        "- **Opportunity score**: geometric mean of the two.\n"
        "- **Underserved**: demand index at least 1.5 and typical index at least 1. "
        "**Hit-driven**: high demand but the typical game is below the overall median. "
        "**Saturated**: demand index below 0.75.\n"
        "- Supply is only the games in the Rotrends top lists, not every game on Roblox."
    )

st.subheader("Most common phrases")
common = table.nlargest(20, "games").sort_values("games")
fig = px.bar(
    common,
    x="games",
    y="phrase",
    orientation="h",
    color_discrete_sequence=[charts.SERIES[0]],
    hover_data={"total_ccu": ":,", "top_game": True},
)
fig.update_xaxes(title="Games using phrase")
fig.update_yaxes(title=None)
st.plotly_chart(charts.style(fig, 520), width="stretch")

st.subheader("Supply vs demand")
fig = px.scatter(
    table,
    x="games",
    y="total_ccu",
    color="verdict",
    size="median_ccu",
    size_max=36,
    log_x=True,
    log_y=True,
    hover_name="phrase",
    hover_data={"top_game": True, "demand_index": ":.2f", "median_ccu": ":,.0f", "verdict": False},
    color_discrete_map=charts.VERDICT_COLORS,
    category_orders={"verdict": charts.VERDICT_ORDER},
)
labelled = table.nlargest(8, "opportunity_score")
for row in labelled.itertuples():
    fig.add_annotation(
        x=row.games, y=row.total_ccu, text=row.phrase, showarrow=False, yshift=14, font_size=11
    )
fig.update_xaxes(title="Games using phrase (supply)")
fig.update_yaxes(title="Total players (demand)")
st.plotly_chart(charts.style(fig, 560), width="stretch")
st.caption(
    "Top-left is the interesting corner: lots of players, few games. Bubble size is median CCU."
)

st.subheader("Ranked by opportunity")
shown = table[["phrase", "verdict", "games", "total_ccu", "median_ccu", "demand_index",
               "typical_index", "opportunity_score", "top_game", "top_game_share",
               "recent_share"]]
st.dataframe(
    shown,
    hide_index=True,
    width="stretch",
    column_config={
        "phrase": "Phrase",
        "verdict": "Verdict",
        "games": "Games",
        "total_ccu": st.column_config.NumberColumn("Total CCU", format="%d"),
        "median_ccu": st.column_config.NumberColumn("Median CCU", format="%d"),
        "demand_index": st.column_config.NumberColumn("Demand index", format="%.2f"),
        "typical_index": st.column_config.NumberColumn("Typical index", format="%.2f"),
        "opportunity_score": st.column_config.NumberColumn("Opportunity", format="%.2f"),
        "top_game": "Biggest game",
        "top_game_share": st.column_config.ProgressColumn(
            "Biggest game's share", min_value=0, max_value=1
        ),
        "recent_share": st.column_config.ProgressColumn(
            "Under 90 days old", min_value=0, max_value=1
        ),
    },
)

st.subheader("Inspect a phrase")
choice = st.selectbox("Phrase", table["phrase"], index=0)
matches = phrase_games(games, choice)
st.dataframe(
    matches[["game_name", "genre", "sub_genre", "players_ccu", "avg_session", "like_ratio",
             "age_days"]],
    hide_index=True,
    width="stretch",
)

st.subheader("Do title tricks matter?")
impact = title_feature_impact(games)
impact["present"] = impact["present"].map({True: "Has it", False: "Doesn't"})
fig = px.bar(
    impact,
    x="feature",
    y="median_ccu",
    color="present",
    barmode="group",
    color_discrete_sequence=charts.SERIES[:2],
    hover_data={"games": True, "avg_like_ratio": ":.2f"},
)
fig.update_xaxes(title=None)
fig.update_yaxes(title="Median CCU")
st.plotly_chart(charts.style(fig, 380), width="stretch")
st.caption(
    "Correlation only. Established hits tend to carry update tags and emoji because they are "
    "updated often, so a gap here does not prove the tag causes players."
)
