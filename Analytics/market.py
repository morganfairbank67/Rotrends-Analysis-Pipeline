import numpy as np
import pandas as pd

RECENT_DAYS = 90


def segment_table(df: pd.DataFrame, by: str, min_games: int = 1) -> pd.DataFrame:
    total_ccu = df["players_ccu"].sum()
    total_games = len(df)
    overall_median = df["players_ccu"].median()
    ordered = df.sort_values("players_ccu", ascending=False)

    grouped = ordered.groupby(by, sort=False)
    table = grouped.agg(
        games=("game_name", "size"),
        total_ccu=("players_ccu", "sum"),
        mean_ccu=("players_ccu", "mean"),
        median_ccu=("players_ccu", "median"),
        top_game=("game_name", "first"),
        top_game_ccu=("players_ccu", "first"),
        avg_like_ratio=("like_ratio", "mean"),
        avg_session=("avg_session", "mean"),
        avg_age_days=("age_days", "mean"),
    )
    table["recent_share"] = grouped["age_days"].apply(lambda s: (s <= RECENT_DAYS).mean())

    table["ccu_share"] = table["total_ccu"] / total_ccu
    table["game_share"] = table["games"] / total_games
    table["demand_index"] = table["ccu_share"] / table["game_share"]
    table["typical_index"] = table["median_ccu"] / overall_median
    table["top_game_share"] = table["top_game_ccu"] / table["total_ccu"].replace(0, np.nan)
    table["opportunity_score"] = np.sqrt(table["demand_index"] * table["typical_index"])
    table["verdict"] = table.apply(classify, axis=1)

    table = table[table["games"] >= min_games]
    return table.sort_values("opportunity_score", ascending=False).reset_index()


def classify(row: pd.Series) -> str:
    if row["demand_index"] >= 1.5:
        return "Underserved" if row["typical_index"] >= 1 else "Hit-driven"
    if row["demand_index"] < 0.75:
        return "Saturated"
    return "Balanced"


def genre_matrix(df: pd.DataFrame, value: str = "players_ccu", agg: str = "sum") -> pd.DataFrame:
    return df.pivot_table(index="genre", columns="sub_genre", values=value, aggfunc=agg)
