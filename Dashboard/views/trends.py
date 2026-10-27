import altair as alt
import pandas as pd
import streamlit as st

from Analytics.prepare import display_title
from Analytics.text import phrase_table
from Analytics.trends import phrase_history, snapshot_dates, snapshot_totals, week_over_week
from Dashboard import charts, ui, viz
from Dashboard.data import current_history

history = current_history()

ui.page_header("Trends", "Change between snapshots")
ui.require_games(history)

dates = snapshot_dates(history)
if len(dates) < 2:
    st.info("At least two snapshots are required for trend analysis.")
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

ui.section("Concurrent players by genre")
by_genre = snapshot_totals(history, by="genre")
biggest = by_genre.groupby("genre")["total_ccu"].sum().nlargest(6).index
viz.show(
    viz.line(
        by_genre[by_genre["genre"].isin(biggest)],
        "extract_date",
        "total_ccu",
        color="genre",
        y_title="Players",
    ),
    height=380,
)

ui.section("Largest changes in players", "Games present in both snapshots")
stayed = wow[wow["status"] == "Still listed"].copy()
stayed["game"] = stayed["game_name"].map(display_title)
movers = pd.concat([
    stayed.nlargest(8, "change").assign(direction="Gained"),
    stayed.nsmallest(8, "change").assign(direction="Lost"),
])
viz.show(
    viz.hbar(
        movers,
        "game",
        "change",
        color="direction",
        scale=alt.Scale(domain=["Gained", "Lost"], range=[charts.SERIES[0], charts.SERIES[1]]),
        label=lambda v: f"{v:+,.0f}",
        x_title="Change in players",
        x_format="~s",
        rule=0,
        tooltip=[
            alt.Tooltip("game:N", title="Game"),
            alt.Tooltip("ccu_before:Q", title="Before", format=","),
            alt.Tooltip("ccu_now:Q", title="Now", format=","),
            alt.Tooltip("change:Q", title="Change", format="+,"),
        ],
    )
)

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
                       "ccu_now": st.column_config.NumberColumn("Players", format="%d")},
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

ui.section("Title phrase trend")
phrases = phrase_table(history[history["extract_date"] == latest], min_games=2)["phrase"].tolist()
if phrases:
    choice = st.selectbox("Phrase", phrases)
    track = phrase_history(history, choice)
    viz.show(
        viz.line(track, "extract_date", "total_ccu", y_title="Players in games using the phrase"),
        height=340,
    )
