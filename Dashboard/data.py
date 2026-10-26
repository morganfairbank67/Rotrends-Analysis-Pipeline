import pandas as pd
import streamlit as st

from Analytics.prepare import prepare
from Cloud_Database import recieveData

GAMES_KEY = "games"
HISTORY_KEY = "history"
FILTER_DEFAULTS = {"f_genres": [], "f_floor": 0, "f_new_only": False, "f_snapshot": None}


@st.cache_data(ttl=600, show_spinner="Loading games from Supabase")
def load_games() -> tuple[pd.DataFrame, int]:
    raw = recieveData.get_data()
    return prepare(raw), len(raw)


def reset_filters() -> None:
    for key, value in FILTER_DEFAULTS.items():
        st.session_state[key] = value


def sidebar_filters(games: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    for key, value in FILTER_DEFAULTS.items():
        st.session_state.setdefault(key, value)

    st.sidebar.markdown("### Filters")

    genres = sorted(games["genre"].unique())
    picked = st.sidebar.multiselect("Genre", genres, key="f_genres", placeholder="All genres")
    if picked:
        games = games[games["genre"].isin(picked)]

    top = int(games["players_ccu"].max()) if len(games) else 0
    floor = st.sidebar.slider("Minimum players", 0, max(top, 1), key="f_floor", step=50)
    games = games[games["players_ccu"] >= floor]

    new_only = st.sidebar.toggle("Released in last 90 days", key="f_new_only")
    if new_only:
        games = games[games["age_days"] <= 90]

    history = games
    dates = sorted(games["extract_date"].dropna().dt.date.unique(), reverse=True)
    if len(dates) > 1:
        chosen = st.sidebar.selectbox("Snapshot", dates, key="f_snapshot")
        current = games[games["extract_date"].dt.date == chosen]
    else:
        current = games

    st.sidebar.button("Reset filters", on_click=reset_filters, width="stretch")
    st.sidebar.caption(f"{len(current):,} games. Scope: Rotrends top lists.")
    return history, current


def current_games() -> pd.DataFrame:
    return st.session_state[GAMES_KEY]


def current_history() -> pd.DataFrame:
    return st.session_state[HISTORY_KEY]
