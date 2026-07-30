import os
import pandas as pd
from dotenv import load_dotenv, find_dotenv
from supabase import Client, create_client

load_dotenv(find_dotenv())
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def get_data():
    dim_resp = supabase.table("dim_games").select("*").execute()
    dim_df = pd.DataFrame(dim_resp.data)

    metrics_resp = supabase.table("game_metrics").select("*").execute()
    metrics_df = pd.DataFrame(metrics_resp.data)

    merged_df = pd.merge(dim_df, metrics_df, on="game_id", how="inner")

    return merged_df

if __name__ == "__main__":
    df = get_data()
    print(df.head())
    print(len())