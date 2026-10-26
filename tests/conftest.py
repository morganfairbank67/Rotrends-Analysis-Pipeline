import pandas as pd
import pytest


def make_row(**overrides):
    row = {
        "game_id": "id",
        "game_name": "Game",
        "category": "Top 100",
        "genre": "Simulation",
        "sub_genre": "Tycoon",
        "created": "2026-06-30",
        "extract_date": "2026-07-30",
        "global_rank": 100,
        "avg_ccu_rank_14d": 100,
        "earning_rank": 50,
        "visits": 1_000_000,
        "players_ccu": 1000,
        "platform_share": 0.001,
        "avg_ccu_1d": 1200,
        "avg_ccu_7d": 1100,
        "avg_ccu_14d": 1000,
        "avg_session": 15.0,
        "favorites": 5000,
        "rating": 0.9,
        "up_votes": 900,
        "down_votes": 100,
    }
    row.update(overrides)
    return row


@pytest.fixture
def raw_games():
    rows = [
        make_row(game_id="1", game_name="Steal a Brainrot", players_ccu=50000, avg_ccu_14d=40000),
        make_row(game_id="2", game_name="Steal a Brainrot", category="Top by Players",
                 earning_rank=None),
        make_row(game_id="3", game_name="[UPD] Tower Defense 🔥", genre="Strategy",
                 sub_genre="Tower Defense", created="2022-01-01", players_ccu=300),
        make_row(game_id="4", game_name="Steal a Fish", players_ccu=200, genre=None,
                 sub_genre=None),
        make_row(game_id="5", game_name="Dead Votes", up_votes=0, down_votes=0, visits=0),
    ]
    return pd.DataFrame(rows)
