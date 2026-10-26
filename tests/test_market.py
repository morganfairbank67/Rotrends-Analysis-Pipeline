import pandas as pd

from Analytics import market


def build(rows):
    df = pd.DataFrame(rows)
    df["like_ratio"] = 0.9
    df["avg_session"] = 10.0
    df["age_days"] = 400
    return df


def test_demand_index_flags_underserved_segment():
    rows = [{"game_name": f"A{i}", "genre": "Hot", "players_ccu": 10000} for i in range(2)]
    rows += [{"game_name": f"B{i}", "genre": "Crowded", "players_ccu": 100} for i in range(8)]
    ranked = market.segment_table(build(rows), "genre")
    assert ranked.loc[0, "genre"] == "Hot"
    table = ranked.set_index("genre")
    assert table.loc["Hot", "demand_index"] > 1.5
    assert table.loc["Hot", "verdict"] == "Underserved"
    assert table.loc["Crowded", "verdict"] == "Saturated"
    assert table.loc["Hot", "opportunity_score"] > table.loc["Crowded", "opportunity_score"]


def test_one_hit_segment_is_marked_hit_driven():
    rows = [{"game_name": "Hit", "genre": "Clones", "players_ccu": 100000}]
    rows += [{"game_name": f"C{i}", "genre": "Clones", "players_ccu": 10} for i in range(4)]
    rows += [{"game_name": f"D{i}", "genre": "Other", "players_ccu": 500} for i in range(20)]
    table = market.segment_table(build(rows), "genre").set_index("genre")
    assert table.loc["Clones", "verdict"] == "Hit-driven"
    assert table.loc["Clones", "top_game_share"] > 0.95


def test_shares_sum_to_one():
    rows = [
        {"game_name": "A", "genre": "X", "players_ccu": 10},
        {"game_name": "B", "genre": "Y", "players_ccu": 30},
    ]
    table = market.segment_table(build(rows), "genre")
    assert abs(table["ccu_share"].sum() - 1) < 1e-9
    assert abs(table["game_share"].sum() - 1) < 1e-9


def test_recent_share_uses_age_cutoff():
    df = build([
        {"game_name": "A", "genre": "X", "players_ccu": 10},
        {"game_name": "B", "genre": "X", "players_ccu": 20},
    ])
    df["age_days"] = [10, 500]
    table = market.segment_table(df, "genre")
    assert table.loc[0, "recent_share"] == 0.5


def test_genre_matrix_pivots_totals():
    df = pd.DataFrame({
        "genre": ["A", "A", "B"],
        "sub_genre": ["x", "y", "x"],
        "players_ccu": [1, 2, 3],
    })
    matrix = market.genre_matrix(df)
    assert matrix.loc["A", "y"] == 2
    assert pd.isna(matrix.loc["B", "y"])
