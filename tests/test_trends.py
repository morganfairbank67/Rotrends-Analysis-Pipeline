import pandas as pd
import pytest

from Analytics import prepare, trends
from tests.conftest import make_row


@pytest.fixture
def history():
    rows = [
        make_row(game_name="Alpha", created="2026-01-01", extract_date="2026-07-23",
                 players_ccu=100),
        make_row(game_name="Beta", created="2026-02-01", extract_date="2026-07-23",
                 players_ccu=400),
        make_row(game_name="Alpha", created="2026-01-01", extract_date="2026-07-30",
                 players_ccu=300),
        make_row(game_name="Steal a Gamma", created="2026-07-20", extract_date="2026-07-30",
                 players_ccu=50),
    ]
    return prepare.prepare(pd.DataFrame(rows))


def test_snapshot_totals_sum_each_week(history):
    totals = trends.snapshot_totals(history)
    assert totals["total_ccu"].tolist() == [500, 350]
    assert totals["games"].tolist() == [2, 2]


def test_snapshot_totals_can_split_by_genre(history):
    totals = trends.snapshot_totals(history, by="genre")
    assert set(totals.columns) >= {"extract_date", "genre", "total_ccu"}


def test_week_over_week_labels_new_dropped_and_staying(history):
    wow = trends.week_over_week(history).set_index("game_name")
    assert wow.loc["Alpha", "status"] == "Still listed"
    assert wow.loc["Alpha", "change"] == 200
    assert wow.loc["Alpha", "pct_change"] == 2
    assert wow.loc["Beta", "status"] == "Dropped out"
    assert wow.loc["Steal a Gamma", "status"] == "New in the lists"


def test_week_over_week_needs_two_snapshots(history):
    single = history[history["extract_date"] == history["extract_date"].max()]
    assert trends.week_over_week(single).empty


def test_game_history_is_ordered(history):
    key = history.loc[history["game_name"] == "Alpha", "game_key"].iloc[0]
    out = trends.game_history(history, key)
    assert out["players_ccu"].tolist() == [100, 300]


def test_phrase_history_counts_matching_games_per_week(history):
    out = trends.phrase_history(history, "steal a")
    assert out["total_ccu"].tolist() == [50]
    assert trends.phrase_history(history, "nothing here").empty
