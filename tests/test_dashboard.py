from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from Cloud_Database import recieveData


def synthetic_raw(n=120, seed=7):
    rng = np.random.default_rng(seed)
    genres = ["Simulation", "Action", "RPG", "Survival"]
    subs = ["Tycoon", "Incremental Simulator", "Action RPG", "1 vs All"]
    words = ["Steal", "Grow", "Escape", "Tower", "Anime", "Simulator", "Defense", "RP"]
    base = pd.Timestamp("2026-07-30")
    rows = []
    for i in range(n):
        ccu = int(rng.lognormal(7, 1.5))
        rows.append({
            "game_id": f"id-{i}",
            "game_name": f"{rng.choice(words)} a {rng.choice(words)} {i % 9}",
            "category": rng.choice(["Top 100", "Top by Players", "Top Moving"]),
            "genre": genres[i % 4],
            "sub_genre": subs[i % 4] if i % 7 else None,
            "created": str(base - pd.Timedelta(days=int(rng.integers(1, 900)))),
            "id": f"m-{i}",
            "global_rank": i + 1,
            "global_rank_shift_1d": 0,
            "global_rank_shift_1w": 0,
            "global_rank_shift_1m": 0,
            "avg_ccu_rank_7d": i + 3,
            "avg_ccu_rank_14d": i + 5,
            "avg_ccu_rank_shift_1d": 0,
            "earning_rank": float(rng.integers(1, 300)) if i % 3 else None,
            "visits": int(rng.integers(10_000, 5_000_000)),
            "players_ccu": ccu,
            "platform_share": ccu / 1e7,
            "avg_ccu_1d": ccu * float(rng.uniform(0.5, 1.8)),
            "avg_ccu_7d": ccu * 0.9,
            "avg_ccu_14d": ccu * float(rng.uniform(0.7, 1.2)),
            "momentum_1d": rng.choice(["Rising", "Stable", "Fading", "Surging"]),
            "momentum_1w": None,
            "momentum_1m": rng.choice(["Rising", "Fading", "Dropping", None]),
            "avg_session": float(rng.uniform(3, 40)),
            "favorites": int(rng.integers(100, 90_000)),
            "rating": 0.9,
            "up_votes": int(rng.integers(100, 9000)),
            "down_votes": int(rng.integers(10, 900)),
            "extract_date": "2026-07-30",
        })
    return pd.DataFrame(rows)


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(recieveData, "get_data", synthetic_raw)
    st.cache_data.clear()
    entry = Path(__file__).resolve().parent.parent / "streamlit_app.py"
    return AppTest.from_file(str(entry), default_timeout=60)


def test_app_renders_without_exceptions(app):
    app.run()
    assert not app.exception
    assert len(app.metric) >= 5


def test_sidebar_genre_filter_narrows_games(app):
    app.run()
    app.sidebar.multiselect[0].set_value(["Action"]).run()
    assert not app.exception
    assert app.metric[0].value == "30"
