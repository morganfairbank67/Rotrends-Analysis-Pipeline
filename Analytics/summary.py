from dataclasses import dataclass

import pandas as pd

from Analytics.market import segment_table
from Analytics.text import phrase_table


@dataclass
class Finding:
    label: str
    headline: str
    detail: str
    page: str


def share(value: float) -> str:
    return f"{value:.0%}" if value >= 0.01 else "<1%"


def underserved_niche(games: pd.DataFrame) -> Finding | None:
    table = segment_table(games, "sub_genre", min_games=3)
    table = table[(table["verdict"] == "Underserved") & (table["sub_genre"] != "Unclassified")]
    if table.empty:
        return None
    row = table.iloc[0]
    return Finding(
        "Biggest gap",
        f"{row['sub_genre']} games",
        f"Only {share(row['game_share'])} of top games, but {share(row['ccu_share'])} of players.",
        "Market gaps",
    )


def underserved_phrase(games: pd.DataFrame) -> Finding | None:
    table = phrase_table(games, min_games=2)
    table = table[(table["verdict"] == "Underserved") & (table["words"] > 1)]
    if table.empty:
        return None
    row = table.iloc[0]
    return Finding(
        "Hot title pattern",
        f"\"{row['phrase']}\"",
        f"{int(row['games'])} games use it and share {int(row['total_ccu']):,} players.",
        "Title keywords",
    )


def fastest_riser(games: pd.DataFrame, min_ccu: int = 500) -> Finding | None:
    eligible = games[(games["players_ccu"] >= min_ccu) & games["ccu_surge"].notna()]
    if eligible.empty:
        return None
    row = eligible.loc[eligible["ccu_surge"].idxmax()]
    return Finding(
        "Fastest riser",
        str(row["display_name"]),
        f"Players are at {row['ccu_surge']:.1f}x its 14-day average.",
        "Engagement",
    )


def most_open_genre(games: pd.DataFrame) -> Finding | None:
    table = segment_table(games, "genre", min_games=5)
    table = table[table["genre"] != "Unknown"]
    if table.empty:
        return None
    row = table.sort_values("recent_share", ascending=False).iloc[0]
    return Finding(
        "Easiest to break into",
        str(row["genre"]),
        f"{share(row['recent_share'])} of its top games are under 90 days old.",
        "Market gaps",
    )


def most_crowded_niche(games: pd.DataFrame) -> Finding | None:
    table = segment_table(games, "sub_genre", min_games=5)
    table = table[(table["verdict"] == "Crowded") & (table["sub_genre"] != "Unclassified")]
    if table.empty:
        return None
    row = table.sort_values("demand_index").iloc[0]
    return Finding(
        "Most crowded",
        f"{row['sub_genre']} games",
        f"{share(row['game_share'])} of top games hold just {share(row['ccu_share'])} of players.",
        "Market gaps",
    )


def headline_findings(games: pd.DataFrame) -> list[Finding]:
    builders = [underserved_niche, underserved_phrase, fastest_riser, most_open_genre,
                most_crowded_niche]
    found = (build(games) for build in builders)
    return [finding for finding in found if finding is not None]
