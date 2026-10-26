import streamlit as st

from Dashboard import theme
from Dashboard.data import GAMES_KEY, HISTORY_KEY, load_games, sidebar_filters

st.set_page_config(
    page_title="Roblox Market Analysis", page_icon=":material/insights:", layout="wide"
)

theme.apply()

try:
    all_games, raw_rows = load_games()
except Exception as error:
    st.error(f"Could not load data from Supabase: {error}")
    st.stop()

history, current = sidebar_filters(all_games)
st.session_state[HISTORY_KEY] = history
st.session_state[GAMES_KEY] = current

pages = [
    st.Page("Dashboard/views/overview.py", title="Overview", icon=":material/dashboard:",
            default=True),
    st.Page("Dashboard/views/market_gaps.py", title="Market gaps", icon=":material/target:"),
    st.Page("Dashboard/views/keywords.py", title="Title keywords", icon=":material/text_fields:"),
    st.Page("Dashboard/views/engagement.py", title="Engagement", icon=":material/groups:"),
    st.Page("Dashboard/views/trends.py", title="Trends", icon=":material/trending_up:"),
]
st.navigation(pages).run()
