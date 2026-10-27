from supabase import Client

from Cloud_Database.client import get_client
from Scraper.validate import ScrapedGameData

METRIC_FIELDS = [
    "extract_date", "global_rank", "global_rank_shift_1d", "global_rank_shift_1w",
    "global_rank_shift_1m", "avg_ccu_rank_7d", "avg_ccu_rank_14d", "avg_ccu_rank_shift_1d",
    "earning_rank", "visits", "players_ccu", "platform_share", "avg_ccu_1d", "avg_ccu_7d",
    "avg_ccu_14d", "momentum_1d", "momentum_1w", "momentum_1m", "avg_session", "favorites",
    "rating", "up_votes", "down_votes",
]


def iso(value):
    return value.isoformat() if value else None


def build_rows(clean_data: list[ScrapedGameData]) -> tuple[list[dict], list[dict]]:
    dim_rows: dict[str, dict] = {}
    categories: dict[str, set] = {}
    metric_rows: dict[tuple, dict] = {}

    for game in clean_data:
        game_id = str(game.game_id)
        categories.setdefault(game_id, set()).add(game.category)
        dim_rows.setdefault(game_id, {
            "game_id": game_id,
            "game_name": game.game_name,
            "genre": game.genre,
            "sub_genre": game.sub_genre,
            "created": iso(game.created),
        })

        row = {"game_id": game_id}
        for field in METRIC_FIELDS:
            value = getattr(game, field)
            row[field] = iso(value) if field == "extract_date" else value
        metric_rows.setdefault((game_id, row["extract_date"]), row)

    for game_id, row in dim_rows.items():
        row["category"] = ", ".join(sorted(categories[game_id]))
    return list(dim_rows.values()), list(metric_rows.values())


def upload_data(clean_data: list[ScrapedGameData], client: Client | None = None):
    client = client or get_client()
    dim_rows, metric_rows = build_rows(clean_data)

    for extract_date in {row["extract_date"] for row in metric_rows}:
        client.table("game_metrics").delete().eq("extract_date", extract_date).execute()

    client.table("dim_games").upsert(dim_rows).execute()
    client.table("game_metrics").insert(metric_rows).execute()
    return len(dim_rows), len(metric_rows)
