import pandas as pd

from Analytics import prepare, text


def test_phrases_keep_articles_inside_ngrams():
    phrases = text.title_phrases("Steal a Brainrot")
    assert "steal a" in phrases
    assert "steal a brainrot" in phrases
    assert "a" not in phrases


def test_bracketed_tags_emoji_and_noise_are_ignored():
    phrases = text.title_phrases("[UPD] 🔥 Tower Defense (Beta) NEW")
    assert phrases == {"tower", "defense", "tower defense"}


def test_ngrams_do_not_cross_separators():
    phrases = text.title_phrases("Speed Keyboard | Candy Chocolate")
    assert "keyboard candy" not in phrases
    assert "speed keyboard" in phrases


def test_non_latin_titles_are_tokenised():
    assert "лагерь" in text.title_phrases("Лагерь РП 🌞")


def test_repeated_word_counts_game_once(raw_games):
    games = prepare.prepare(raw_games.head(1).assign(game_name="Tower Tower Tower"))
    table = text.phrase_table(games, sizes=(1,), min_games=1)
    assert table.loc[table["phrase"] == "tower", "games"].iloc[0] == 1


def test_phrase_table_counts_games_and_demand(raw_games):
    games = prepare.prepare(raw_games)
    table = text.phrase_table(games, sizes=(1, 2), min_games=2)
    steal = table[table["phrase"] == "steal a"].iloc[0]
    assert steal["games"] == 2
    assert steal["total_ccu"] == 50000 + 200
    assert steal["top_game"] == "Steal a Brainrot"
    assert steal["top_game_share"] > 0.99


def test_phrase_table_respects_min_games(raw_games):
    games = prepare.prepare(raw_games)
    table = text.phrase_table(games, min_games=3)
    assert table.empty


def test_phrase_games_lists_matches_by_ccu(raw_games):
    games = prepare.prepare(raw_games)
    found = text.phrase_games(games, "steal a")
    assert list(found["game_name"]) == ["Steal a Brainrot", "Steal a Fish"]
    assert isinstance(found, pd.DataFrame)


def test_phrases_shared_by_the_same_games_collapse_to_the_longest(raw_games):
    rows = raw_games.head(2).assign(game_name=["Red Tower Rush", "Red Tower Run"])
    rows["created"] = ["2026-01-01", "2026-02-02"]
    table = text.phrase_table(prepare.prepare(rows), min_games=2)
    assert table["phrase"].tolist() == ["red tower"]
    uncollapsed = text.phrase_table(prepare.prepare(rows), min_games=2, collapse=False)
    assert set(uncollapsed["phrase"]) == {"red", "tower", "red tower"}
