import streamlit as st

from Dashboard.data import SESSION_KEY, load_games, sidebar_filters

st.set_page_config(page_title="Rotrends Market Analysis", page_icon="📊", layout="wide")

try:
    games, raw_rows = load_games()
except Exception as error:
    st.error(f"Could not load data from Supabase: {error}")
    st.stop()

st.session_state[SESSION_KEY] = sidebar_filters(games)
st.sidebar.caption(f"{raw_rows:,} raw rows across all snapshots")

pages = [
    st.Page("Dashboard/views/overview.py", title="Overview", icon="📊", default=True),
    st.Page("Dashboard/views/keywords.py", title="Title keywords", icon="🔤"),
    st.Page("Dashboard/views/market_gaps.py", title="Market gaps", icon="🎯"),
]
st.navigation(pages).run()
