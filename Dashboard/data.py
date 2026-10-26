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

    st.sidebar.markdown("### Filter the data")

    genres = sorted(games["genre"].unique())
    picked = st.sidebar.multiselect(
        "Genre", genres, key="f_genres", placeholder="All genres",
        help="Leave empty to include every genre.",
    )
    if picked:
        games = games[games["genre"].isin(picked)]

    top = int(games["players_ccu"].max()) if len(games) else 0
    floor = st.sidebar.slider(
        "Minimum players online now", 0, max(top, 1), key="f_floor", step=50,
        help="Hide small games. 0 keeps everything.",
    )
    games = games[games["players_ccu"] >= floor]

    new_only = st.sidebar.toggle(
        "Only games under 90 days old", key="f_new_only",
        help="Focus on recent releases to see what newcomers are doing.",
    )
    if new_only:
        games = games[games["age_days"] <= 90]

    history = games
    dates = sorted(games["extract_date"].dropna().dt.date.unique(), reverse=True)
    if len(dates) > 1:
        chosen = st.sidebar.selectbox(
            "Weekly snapshot", dates, key="f_snapshot",
            help="Each weekly scrape is one snapshot. Trends compares them all.",
        )
        current = games[games["extract_date"].dt.date == chosen]
    else:
        current = games

    st.sidebar.button("Reset filters", on_click=reset_filters, width="stretch")
    st.sidebar.caption(f"Showing {len(current):,} games")
    return history, current


def current_games() -> pd.DataFrame:
    return st.session_state[GAMES_KEY]


def current_history() -> pd.DataFrame:
    return st.session_state[HISTORY_KEY]
