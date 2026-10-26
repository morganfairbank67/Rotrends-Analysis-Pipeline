import numpy as np
import pandas as pd

from Analytics.text import title_phrases


def snapshot_dates(history: pd.DataFrame) -> list[pd.Timestamp]:
    return sorted(history["extract_date"].dropna().unique())


def snapshot_totals(history: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    keys = ["extract_date"] + ([by] if by else [])
    table = history.groupby(keys).agg(
        games=("game_key", "nunique"),
        total_ccu=("players_ccu", "sum"),
        median_ccu=("players_ccu", "median"),
    )
    return table.reset_index()


def week_over_week(history: pd.DataFrame) -> pd.DataFrame:
    dates = snapshot_dates(history)
    if len(dates) < 2:
        return pd.DataFrame()
    before = history[history["extract_date"] == dates[-2]]
    now = history[history["extract_date"] == dates[-1]]
    columns = ["game_key", "game_name", "genre", "sub_genre", "players_ccu"]
    merged = now[columns].merge(
        before[["game_key", "game_name", "genre", "sub_genre", "players_ccu"]],
        on="game_key",
        how="outer",
        suffixes=("", "_before"),
    )
    merged["game_name"] = merged["game_name"].fillna(merged["game_name_before"])
    merged["genre"] = merged["genre"].fillna(merged["genre_before"])
    merged["sub_genre"] = merged["sub_genre"].fillna(merged["sub_genre_before"])
    merged = merged.rename(columns={"players_ccu": "ccu_now", "players_ccu_before": "ccu_before"})
    merged["status"] = np.select(
        [merged["ccu_before"].isna(), merged["ccu_now"].isna()],
        ["New in the lists", "Dropped out"],
        default="Still listed",
    )
    merged["change"] = merged["ccu_now"].fillna(0) - merged["ccu_before"].fillna(0)
    merged["pct_change"] = merged["change"] / merged["ccu_before"].replace(0, np.nan)
    keep = ["game_key", "game_name", "genre", "sub_genre", "ccu_before", "ccu_now", "change",
            "pct_change", "status"]
    return merged[keep]


def game_history(history: pd.DataFrame, game_key: str) -> pd.DataFrame:
    rows = history[history["game_key"] == game_key]
    return rows.sort_values("extract_date")[["extract_date", "players_ccu", "avg_ccu_14d",
                                             "global_rank"]]


def phrase_history(history: pd.DataFrame, phrase: str) -> pd.DataFrame:
    mask = history["game_name"].fillna("").map(lambda t: phrase in title_phrases(t))
    matched = history[mask]
    if matched.empty:
        return pd.DataFrame(columns=["extract_date", "games", "total_ccu"])
    table = matched.groupby("extract_date").agg(
        games=("game_key", "nunique"), total_ccu=("players_ccu", "sum")
    )
    return table.reset_index()
