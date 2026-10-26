import numpy as np

from Analytics import prepare


def test_collapse_merges_list_appearances(raw_games):
    out = prepare.collapse_list_appearances(raw_games)
    brainrot = out[out["game_name"] == "Steal a Brainrot"].iloc[0]
    assert len(out) == 4
    assert brainrot["list_count"] == 2
    assert brainrot["categories"] == "Top 100, Top by Players"
    assert brainrot["earning_rank"] == 50


def test_missing_genres_get_placeholder_labels(raw_games):
    out = prepare.prepare(raw_games)
    fish = out[out["game_name"] == "Steal a Fish"].iloc[0]
    assert fish["genre"] == "Unknown"
    assert fish["sub_genre"] == "Unclassified"


def test_age_and_release_flags(raw_games):
    out = prepare.prepare(raw_games).set_index("game_name")
    assert out.loc["Steal a Brainrot", "age_days"] == 30
    assert bool(out.loc["Steal a Brainrot", "is_new_release"])
    assert out.loc["[UPD] Tower Defense 🔥", "age_bucket"] == "3+ years"
    assert not bool(out.loc["[UPD] Tower Defense 🔥", "is_new_release"])


def test_ratio_features_avoid_division_by_zero(raw_games):
    out = prepare.prepare(raw_games).set_index("game_name")
    assert np.isnan(out.loc["Dead Votes", "like_ratio"])
    assert np.isnan(out.loc["Dead Votes", "favorites_per_1k_visits"])
    assert out.loc["Steal a Fish", "like_ratio"] == 0.9


def test_title_flags(raw_games):
    out = prepare.prepare(raw_games).set_index("game_name")
    tagged = out.loc["[UPD] Tower Defense 🔥"]
    assert bool(tagged["has_emoji"])
    assert bool(tagged["has_brackets"])
    assert bool(tagged["has_update_tag"])
    plain = out.loc["Steal a Fish"]
    assert not bool(plain["has_emoji"])
    assert not bool(plain["has_update_tag"])


def test_latest_snapshot_keeps_newest_extract(raw_games):
    raw_games.loc[0, "extract_date"] = "2026-07-01"
    out = prepare.latest_snapshot(prepare.prepare(raw_games))
    assert (out["extract_date"] == out["extract_date"].max()).all()
    assert len(out) == 4


def test_game_key_ignores_title_tags_and_emoji():
    assert prepare.core_title("[UPD] 🔥 Fish It! 🐟") == "fish it"
    assert prepare.core_title("Fish It!") == "fish it"


def test_same_game_with_changed_title_collapses(raw_games):
    rows = raw_games.head(2).copy()
    rows["game_name"] = ["Fish It!", "[UPD] Fish It! 🐟"]
    out = prepare.collapse_list_appearances(rows)
    assert len(out) == 1
    assert out.iloc[0]["list_count"] == 2


def test_same_title_with_different_release_date_stays_separate(raw_games):
    rows = raw_games.head(2).copy()
    rows["game_name"] = "Obby"
    rows["created"] = ["2025-01-01", "2026-01-01"]
    assert len(prepare.collapse_list_appearances(rows)) == 2


def test_display_title_strips_tags_and_emoji_but_keeps_plain_titles():
    assert prepare.display_title("[W2] +1 Speed Shinobi Escape") == "1 Speed Shinobi Escape"
    assert prepare.display_title("🌻 [PETS] Pet Simulator 99! ⚔️") == "Pet Simulator 99!"
    assert prepare.display_title("[UPD]") == "[UPD]"
