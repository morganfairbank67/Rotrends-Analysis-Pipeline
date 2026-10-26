import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

TITLE_FLAGS = {
    "has_emoji": "Emoji in title",
    "has_brackets": "Bracketed tag",
    "has_update_tag": "Update / new tag",
}
CLUSTER_FEATURES = [
    "players_ccu",
    "avg_session",
    "like_ratio",
    "favorites_per_1k_visits",
    "age_days",
]
LOG_FEATURES = {"players_ccu", "favorites_per_1k_visits", "age_days"}


def title_feature_impact(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column, label in TITLE_FLAGS.items():
        for flag, group in df.groupby(column):
            rows.append({
                "feature": label,
                "present": bool(flag),
                "games": len(group),
                "median_ccu": group["players_ccu"].median(),
                "mean_ccu": group["players_ccu"].mean(),
                "avg_like_ratio": group["like_ratio"].mean(),
                "avg_age_days": group["age_days"].mean(),
            })
    return pd.DataFrame(rows)


def age_cohorts(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("age_bucket", observed=False)
    table = grouped.agg(
        games=("game_name", "size"),
        total_ccu=("players_ccu", "sum"),
        median_ccu=("players_ccu", "median"),
        avg_session=("avg_session", "mean"),
        avg_like_ratio=("like_ratio", "mean"),
    ).reset_index()
    table["ccu_share"] = table["total_ccu"] / table["total_ccu"].sum()
    table["game_share"] = table["games"] / table["games"].sum()
    return table


def top_movers(
    df: pd.DataFrame, min_ccu: int = 500, n: int = 15
) -> tuple[pd.DataFrame, pd.DataFrame]:
    eligible = df[(df["players_ccu"] >= min_ccu) & df["ccu_surge"].notna()]
    columns = ["game_name", "genre", "sub_genre", "players_ccu", "avg_ccu_14d", "ccu_surge"]
    rising = eligible.nlargest(n, "ccu_surge")[columns]
    fading = eligible.nsmallest(n, "ccu_surge")[columns]
    return rising, fading


def momentum_mix(df: pd.DataFrame, by: str = "genre", column: str = "momentum_1m") -> pd.DataFrame:
    known = df.dropna(subset=[column])
    return pd.crosstab(known[by], known[column], normalize="index")


def monetisation_leaders(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    scored = df.dropna(subset=["monetisation_gap"])
    columns = ["game_name", "genre", "players_ccu", "avg_ccu_rank_14d", "earning_rank",
               "monetisation_gap"]
    return scored.nlargest(n, "monetisation_gap")[columns]


def cluster_games(df: pd.DataFrame, k: int = 4, seed: int = 42) -> pd.DataFrame:
    usable = df.dropna(subset=CLUSTER_FEATURES).copy()
    if len(usable) < k:
        raise ValueError("not enough complete rows to form that many clusters")
    matrix = usable[CLUSTER_FEATURES].copy()
    for column in LOG_FEATURES:
        matrix[column] = np.log1p(matrix[column])
    scaled = StandardScaler().fit_transform(matrix)
    usable["cluster"] = KMeans(n_clusters=k, random_state=seed, n_init=10).fit_predict(scaled)
    return usable


def describe_cluster(row: pd.Series, overall: pd.Series) -> str:
    size = "Big" if row["players_ccu"] >= overall["players_ccu"] else "Small"
    session = "long" if row["avg_session"] >= overall["avg_session"] else "short"
    age = "newer" if row["age_days"] < overall["age_days"] else "older"
    return f"{size} games, {session} sessions, {age}"


def cluster_profile(clustered: pd.DataFrame) -> pd.DataFrame:
    grouped = clustered.groupby("cluster")
    profile = grouped[CLUSTER_FEATURES].median()
    overall = clustered[CLUSTER_FEATURES].median()
    profile.insert(0, "games", grouped.size())
    profile["top_genre"] = grouped["genre"].agg(lambda s: s.value_counts().index[0])
    profile["description"] = profile.apply(describe_cluster, axis=1, overall=overall)
    return profile.reset_index()


def metric_links(df: pd.DataFrame, target: str, metrics: list[str]) -> pd.DataFrame:
    rows = []
    for metric in metrics:
        if metric == target:
            continue
        pair = df[[target, metric]].dropna()
        if len(pair) < 10:
            continue
        rows.append({"metric": metric, "correlation": pair[target].corr(pair[metric],
                                                                       method="spearman")})
    table = pd.DataFrame(rows, columns=["metric", "correlation"]).dropna()
    return table.reindex(table["correlation"].abs().sort_values().index).reset_index(drop=True)


def list_overlap(df: pd.DataFrame) -> pd.DataFrame:
    table = df.groupby("categories").agg(
        games=("game_name", "size"),
        median_ccu=("players_ccu", "median"),
    )
    return table.sort_values("games", ascending=False).reset_index()
