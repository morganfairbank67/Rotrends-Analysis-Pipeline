import pandas as pd
import plotly.express as px
import streamlit as st

from Analytics.prepare import display_title
from Analytics.text import phrase_table
from Analytics.trends import phrase_history, snapshot_dates, snapshot_totals, week_over_week
from Dashboard import charts, ui
from Dashboard.data import current_history

history = current_history()

ui.page_header("Trends", "What has changed since the last weekly snapshot?")
ui.require_games(history)

dates = snapshot_dates(history)
if len(dates) < 2:
    st.info(
        "Trends need at least two weekly snapshots to compare. A new snapshot is collected "
        "automatically every Monday, so check back after the next run.",
        icon="⏳",
    )
    st.stop()

wow = week_over_week(history)
latest, previous = dates[-1], dates[-2]
st.caption(
    f"Comparing {latest.strftime('%d %b %Y')} with {previous.strftime('%d %b %Y')}."
)

totals = snapshot_totals(history)
change = totals["total_ccu"].iloc[-1] - totals["total_ccu"].iloc[-2]
cols = st.columns(3)
cols[0].metric("Players across tracked games", ui.compact(totals["total_ccu"].iloc[-1]),
               delta=ui.compact(change))
cols[1].metric("New in the lists", int((wow["status"] == "New in the lists").sum()))
cols[2].metric("Dropped out", int((wow["status"] == "Dropped out").sum()))

ui.section("Players over time", "Total players online across the tracked games, by genre.")
by_genre = snapshot_totals(history, by="genre")
biggest = by_genre.groupby("genre")["total_ccu"].sum().nlargest(6).index
fig = px.line(
    by_genre[by_genre["genre"].isin(biggest)],
    x="extract_date",
    y="total_ccu",
    color="genre",
    markers=True,
    color_discrete_sequence=charts.SERIES,
)
fig.update_xaxes(title=None)
fig.update_yaxes(title="Players online")
charts.show(fig, 420)

ui.section("Biggest movers", "Games that were in both snapshots, by change in players online.")
stayed = wow[wow["status"] == "Still listed"].copy()
stayed["game"] = stayed["game_name"].map(display_title)
movers = pd.concat([
    stayed.nlargest(8, "change").assign(direction="Gained"),
    stayed.nsmallest(8, "change").assign(direction="Lost"),
])
fig = px.bar(
    movers.sort_values("change"),
    x="change",
    y="game",
    color="direction",
    orientation="h",
    color_discrete_map={"Gained": charts.SERIES[0], "Lost": charts.SERIES[1]},
)
fig.update_xaxes(title="Change in players online")
fig.update_yaxes(title=None)
charts.show(fig, 520)

new_col, gone_col = st.columns(2)
fresh = wow[wow["status"] == "New in the lists"].nlargest(10, "ccu_now")
gone = wow[wow["status"] == "Dropped out"].nlargest(10, "ccu_before")
with new_col:
    st.markdown("**New in the lists**")
    st.dataframe(
        fresh.assign(game=fresh["game_name"].map(display_title))[["game", "genre", "ccu_now"]],
        hide_index=True,
        width="stretch",
        column_config={"game": "Game", "genre": "Genre",
                       "ccu_now": st.column_config.NumberColumn("Players now", format="%d")},
    )
with gone_col:
    st.markdown("**Dropped out**")
    st.dataframe(
        gone.assign(game=gone["game_name"].map(display_title))[["game", "genre", "ccu_before"]],
        hide_index=True,
        width="stretch",
        column_config={"game": "Game", "genre": "Genre",
                       "ccu_before": st.column_config.NumberColumn("Players before", format="%d")},
    )

ui.section("Track a title pattern", "Is a phrase gaining or losing players week by week?")
phrases = phrase_table(history[history["extract_date"] == latest], min_games=2)["phrase"].tolist()
if phrases:
    choice = st.selectbox("Phrase", phrases)
    track = phrase_history(history, choice)
    fig = px.line(track, x="extract_date", y="total_ccu", markers=True,
                  color_discrete_sequence=[charts.SERIES[0]])
    fig.update_xaxes(title=None)
    fig.update_yaxes(title="Players online in games using it")
    charts.show(fig, 360)
