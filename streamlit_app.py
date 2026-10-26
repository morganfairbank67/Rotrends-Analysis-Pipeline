import streamlit as st

from Dashboard.data import GAMES_KEY, HISTORY_KEY, load_games, sidebar_filters

st.set_page_config(page_title="Roblox Market Gap Finder", page_icon="📊", layout="wide")

try:
    all_games, raw_rows = load_games()
except Exception as error:
    st.error(f"Could not load data from Supabase: {error}")
    st.stop()

history, current = sidebar_filters(all_games)
st.session_state[HISTORY_KEY] = history
st.session_state[GAMES_KEY] = current

pages = {
    "Start": [
        st.Page("Dashboard/views/home.py", title="Start here", icon="🏠", default=True),
    ],
    "Explore": [
        st.Page("Dashboard/views/overview.py", title="Market overview", icon="📊"),
        st.Page("Dashboard/views/market_gaps.py", title="Market gaps", icon="🎯"),
        st.Page("Dashboard/views/keywords.py", title="Title keywords", icon="🔤"),
    ],
    "Go deeper": [
        st.Page("Dashboard/views/engagement.py", title="Engagement", icon="🎮"),
    ],
}
st.navigation(pages).run()
