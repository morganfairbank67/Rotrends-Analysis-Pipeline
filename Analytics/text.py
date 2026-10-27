import re

import pandas as pd

from Analytics.identity import BRACKETED, is_emoji
from Analytics.market import segment_table

SEGMENT_BREAKS = re.compile(r"[|:/&,!?.\-–—~•+]+")
WORD = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)?")

STOPWORDS = frozenset(
    "a an the of to for in on and or is at by with my your from vs it its be this that".split()
)
NOISE = frozenset(
    "upd update updates new release event beta alpha code codes free official".split()
)


def title_segments(title: str) -> list[list[str]]:
    text = BRACKETED.sub(" ", title.lower())
    text = "".join(" " if is_emoji(c) else c for c in text)
    segments = []
    for chunk in SEGMENT_BREAKS.split(text):
        words = WORD.findall(chunk)
        if words:
            segments.append(words)
    return segments


def title_phrases(title: str, sizes: tuple[int, ...] = (1, 2, 3)) -> set[str]:
    phrases = set()
    for words in title_segments(title):
        for size in sizes:
            for start in range(len(words) - size + 1):
                gram = words[start:start + size]
                if any(w in NOISE for w in gram):
                    continue
                if all(w in STOPWORDS for w in gram):
                    continue
                phrases.add(" ".join(gram))
    return phrases


def explode_phrases(df: pd.DataFrame, sizes: tuple[int, ...] = (1, 2, 3)) -> pd.DataFrame:
    out = df.copy()
    out["phrase"] = out["game_name"].fillna("").map(lambda t: sorted(title_phrases(t, sizes)))
    out = out.explode("phrase").dropna(subset=["phrase"])
    out["words"] = out["phrase"].str.count(" ") + 1
    return out


def phrase_table(
    df: pd.DataFrame,
    sizes: tuple[int, ...] = (1, 2, 3),
    min_games: int = 2,
    collapse: bool = True,
) -> pd.DataFrame:
    exploded = explode_phrases(df, sizes)
    table = segment_table(exploded, "phrase", min_games=min_games)
    table["words"] = table["phrase"].str.count(" ") + 1
    if collapse:
        table = (
            table.sort_values("words", ascending=False)
            .drop_duplicates(["games", "total_ccu", "top_game"])
            .sort_values("opportunity_score", ascending=False)
            .reset_index(drop=True)
        )
    return table


def phrase_games(df: pd.DataFrame, phrase: str) -> pd.DataFrame:
    mask = df["game_name"].fillna("").map(lambda t: phrase in title_phrases(t))
    return df[mask].sort_values("players_ccu", ascending=False)
