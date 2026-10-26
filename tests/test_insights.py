import numpy as np
import pandas as pd
import pytest

from Analytics import insights, prepare
from tests.conftest import make_row


@pytest.fixture
def games():
    rows = []
    for i in range(24):
        rows.append(make_row(
            game_id=str(i),
            game_name=f"[UPD] Game {i}" if i % 3 == 0 else f"Game {i}",
            created=f"2026-0{1 + i % 6}-15",
            players_ccu=100 * (i + 1),
            avg_ccu_1d=100 * (i + 1) * (0.5 + i / 20),
            avg_ccu_14d=100 * (i + 1),
            avg_session=5.0 + i,
            up_votes=800 + i * 10,
            favorites=1000 + 50 * i,
            genre="A" if i % 2 else "B",
        ))
    return prepare.prepare(pd.DataFrame(rows))


def test_title_feature_impact_splits_present_and_absent(games):
    table = insights.title_feature_impact(games)
    update = table[table["feature"] == "Update / new tag"].set_index("present")
    assert update.loc[True, "games"] == 8
    assert update.loc[False, "games"] == 16


def test_age_cohorts_cover_every_game(games):
    table = insights.age_cohorts(games)
    assert table["games"].sum() == len(games)
    assert abs(table["ccu_share"].sum() - 1) < 1e-9


def test_top_movers_orders_by_surge_and_respects_floor(games):
    rising, fading = insights.top_movers(games, min_ccu=500, n=3)
    assert rising["ccu_surge"].is_monotonic_decreasing
    assert fading["ccu_surge"].is_monotonic_increasing
    assert (rising["players_ccu"] >= 500).all()


def test_momentum_mix_rows_sum_to_one():
    df = pd.DataFrame({
        "genre": ["A", "A", "B"],
        "momentum_1m": ["Rising", "Fading", "Rising"],
    })
    mix = insights.momentum_mix(df)
    assert np.allclose(mix.sum(axis=1), 1)
    assert mix.loc["B", "Rising"] == 1


def test_monetisation_leaders_rank_by_gap(games):
    games.loc[0, "monetisation_gap"] = 899
    leaders = insights.monetisation_leaders(games, n=2)
    assert leaders.iloc[0]["game_name"] == games.loc[0, "game_name"]
    assert leaders["monetisation_gap"].is_monotonic_decreasing


def test_clusters_assign_every_complete_row(games):
    clustered = insights.cluster_games(games, k=3)
    assert clustered["cluster"].nunique() == 3
    assert len(clustered) == len(games)
    profile = insights.cluster_profile(clustered)
    assert profile["games"].sum() == len(games)


def test_clusters_reject_too_few_rows(games):
    with pytest.raises(ValueError):
        insights.cluster_games(games.head(2), k=4)


def test_list_overlap_counts_combinations(games):
    games.loc[:2, "categories"] = "Top 100, Top by Players"
    table = insights.list_overlap(games)
    assert table.iloc[0]["games"] == 21
