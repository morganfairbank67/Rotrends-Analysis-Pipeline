import pandas as pd
import streamlit as st

from Analytics.prepare import latest_snapshot, prepare
from Cloud_Database.recieveData import get_data

SESSION_KEY = "games"


@st.cache_data(ttl=600, show_spinner="Loading games from Supabase")
def load_games() -> tuple[pd.DataFrame, int]:
    raw = get_data()
    return prepare(raw), len(raw)


def sidebar_filters(games: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    dates = sorted(games["extract_date"].dropna().dt.date.unique())
    if len(dates) > 1:
        chosen = st.sidebar.selectbox("Snapshot", dates[::-1])
        games = games[games["extract_date"].dt.date == chosen]
    else:
        games = latest_snapshot(games)

    genres = sorted(games["genre"].unique())
    picked = st.sidebar.multiselect("Genres", genres, placeholder="All genres")
    if picked:
        games = games[games["genre"].isin(picked)]

    top = int(games["players_ccu"].max())
    floor = st.sidebar.slider("Minimum concurrent players", 0, max(top, 1), 0, step=50)
    games = games[games["players_ccu"] >= floor]

    new_only = st.sidebar.toggle("Released in the last 90 days only")
    if new_only:
        games = games[games["age_days"] <= 90]

    st.sidebar.caption(f"{len(games):,} games after filters")
    return games


def current_games() -> pd.DataFrame:
    return st.session_state[SESSION_KEY]
