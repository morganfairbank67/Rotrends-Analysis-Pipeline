import streamlit as st

from Analytics.summary import headline_findings
from Analytics.trends import snapshot_dates
from Dashboard import ui
from Dashboard.data import current_games, current_history

games = current_games()
history = current_history()

ui.page_header(
    "Roblox market gap finder",
    "Where are lots of players with too few games to play?",
)
st.markdown(
    "Every week this project collects the top Roblox games from Rotrends, cleans the data and "
    "stores it in a database. This dashboard turns that data into answers about which kinds "
    "of game players want most and which are already crowded."
)

ui.require_games(games)

latest = games["extract_date"].max().strftime("%d %b %Y")
cols = st.columns(4)
cols[0].metric("Games analysed", f"{len(games):,}")
cols[1].metric("Players online", ui.compact(games["players_ccu"].sum()))
cols[2].metric("Latest snapshot", latest)
cols[3].metric("Weekly snapshots", len(snapshot_dates(history)))

st.subheader("What the data says right now")
findings = headline_findings(games)
if findings:
    for column, finding in zip(st.columns(len(findings)), findings, strict=True):
        with column.container(border=True):
            st.caption(finding.label.upper())
            st.markdown(f"**{finding.headline}**")
            st.write(finding.detail)
else:
    st.info("Not enough games under the current filters to pick out highlights.")

st.subheader("Where to go next")
left, right = st.columns(2)
with left.container(border=True):
    st.markdown("**Is a niche under-served?**")
    st.write("Compare each genre's share of players with its share of games.")
    st.page_link("Dashboard/views/market_gaps.py", label="Open Market gaps", icon="🎯")
with right.container(border=True):
    st.markdown("**What are games called?**")
    st.write("See which words and patterns, like \"steal a\", pull the most players.")
    st.page_link("Dashboard/views/keywords.py", label="Open Title keywords", icon="🔤")

with st.expander("Plain-English glossary"):
    st.markdown(
        "- **Players online (CCU)**: how many people are in a game at the moment of the snapshot.\n"
        "- **Under-served**: a group of games holding more than its fair share of players "
        "compared with how many games it has.\n"
        "- **Crowded**: many games splitting a small share of players.\n"
        "- **Hit-driven**: one huge game props up the group while the rest struggle.\n"
        "- **Snapshot**: one weekly copy of the Rotrends top lists."
    )
    st.caption(
        "Only games in the Rotrends top lists are counted, so \"few games\" means few top games, "
        "not few games on all of Roblox."
    )
