import os

from dotenv import load_dotenv, find_dotenv
from supabase import Client, create_client
from Scraper.validate import ScrapedGameData

load_dotenv(find_dotenv())

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def upload_data(clean_data: list[ScrapedGameData]):
    dim_games_list = []
    game_metric_list = []

    for game in clean_data:
        dim_row = {
            "game_id": str(game.game_id),
            "game_name": game.game_name,
            "category": game.category,
            "genre": game.genre,
            "sub_genre": game.sub_genre,
            "created": game.created.isoformat() if game.created else None
        }
    
        dim_games_list.append(dim_row)

        game_row = {
            "game_id": str(game.game_id),
            "extract_date": game.extract_date.isoformat() if game.extract_date else None,
            "global_rank": game.global_rank,
            "global_rank_shift_1d": game.global_rank_shift_1d,
            "global_rank_shift_1w": game.global_rank_shift_1w,
            "global_rank_shift_1m": game.global_rank_shift_1m,
            "avg_ccu_rank_7d": game.avg_ccu_rank_7d,
            "avg_ccu_rank_14d": game.avg_ccu_rank_14d,
            "avg_ccu_rank_shift_1d": game.avg_ccu_rank_shift_1d,
            "earning_rank": game.earning_rank,
            "visits": game.visits,
            "players_ccu": game.players_ccu,
            "platform_share": game.platform_share,
            "avg_ccu_1d": game.avg_ccu_1d,
            "avg_ccu_7d": game.avg_ccu_7d,
            "avg_ccu_14d": game.avg_ccu_14d,
            "momentum_1d": game.momentum_1d,
            "momentum_1w": game.momentum_1w,
            "momentum_1m": game.momentum_1m,
            "avg_session": game.avg_session,
            "favorites": game.favorites,
            "rating": game.rating,
            "up_votes": game.up_votes,
            "down_votes": game.down_votes
        }

        game_metric_list.append(game_row)

    supabase.table("dim_games").upsert(dim_games_list).execute()
    supabase.table("game_metrics").upsert(game_metric_list).execute()
    