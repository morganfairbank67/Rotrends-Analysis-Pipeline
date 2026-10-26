import re
import unicodedata

import numpy as np
import pandas as pd

BRACKETED = re.compile(r"\[[^\]]*\]|\([^)]*\)")
NON_WORD = re.compile(r"[\W_]+")
IDENTITY_COLUMNS = ["game_key", "extract_date"]
AGE_BINS = [-1, 30, 90, 365, 1095, np.inf]
AGE_LABELS = ["< 1 month", "1-3 months", "3-12 months", "1-3 years", "3+ years"]


def is_emoji(char: str) -> bool:
    return unicodedata.category(char) == "So" or ord(char) >= 0x1F000


def core_title(title: str) -> str:
    text = BRACKETED.sub(" ", str(title).lower())
    text = "".join(" " if is_emoji(c) else c for c in text)
    return NON_WORD.sub(" ", text).strip()


def add_game_key(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    created = pd.to_datetime(out["created"], errors="coerce").dt.strftime("%Y-%m-%d")
    out["game_key"] = out["game_name"].map(core_title) + "|" + created.fillna("unknown")
    return out


def collapse_list_appearances(df: pd.DataFrame) -> pd.DataFrame:
    df = add_game_key(df)
    grouped = df.groupby(IDENTITY_COLUMNS, sort=False, dropna=False)
    collapsed = grouped.first().reset_index()
    collapsed["categories"] = grouped["category"].agg(lambda s: ", ".join(sorted(set(s)))).values
    collapsed["list_count"] = grouped["category"].nunique().values
    return collapsed.drop(columns=["category"])


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["created"] = pd.to_datetime(out["created"], errors="coerce")
    out["extract_date"] = pd.to_datetime(out["extract_date"], errors="coerce")
    out["genre"] = out["genre"].fillna("Unknown")
    out["sub_genre"] = out["sub_genre"].fillna("Unclassified")

    out["age_days"] = (out["extract_date"] - out["created"]).dt.days.clip(lower=0)
    out["age_bucket"] = pd.cut(out["age_days"], bins=AGE_BINS, labels=AGE_LABELS)

    votes = out["up_votes"] + out["down_votes"]
    out["total_votes"] = votes
    out["like_ratio"] = (out["up_votes"] / votes.replace(0, np.nan))
    out["favorites_per_1k_visits"] = out["favorites"] / out["visits"].replace(0, np.nan) * 1000
    out["visits_per_ccu"] = out["visits"] / out["players_ccu"].replace(0, np.nan)
    out["ccu_surge"] = out["avg_ccu_1d"] / out["avg_ccu_14d"].replace(0, np.nan)
    out["ccu_vs_14d"] = out["players_ccu"] / out["avg_ccu_14d"].replace(0, np.nan)
    out["monetisation_gap"] = out["avg_ccu_rank_14d"] - out["earning_rank"]
    out["share_pct"] = out["platform_share"] * 100

    titles = out["game_name"].fillna("")
    out["title_length"] = titles.str.len()
    out["has_emoji"] = titles.map(lambda t: any(is_emoji(c) for c in t))
    out["has_brackets"] = titles.str.contains(r"[\[\(]", regex=True)
    out["has_update_tag"] = titles.str.contains(r"\b(?:upd|update|new|release)\b", case=False)
    out["is_new_release"] = out["age_days"] <= 30
    return out


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    return add_features(collapse_list_appearances(df))


def latest_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["extract_date"] == df["extract_date"].max()]
