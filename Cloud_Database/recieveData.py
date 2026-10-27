import pandas as pd
from supabase import Client

from Cloud_Database.client import get_client

PAGE_SIZE = 1000


def fetch_table(client: Client, table: str) -> pd.DataFrame:
    rows = []
    start = 0
    while True:
        resp = client.table(table).select("*").range(start, start + PAGE_SIZE - 1).execute()
        rows.extend(resp.data)
        if len(resp.data) < PAGE_SIZE:
            break
        start += PAGE_SIZE
    return pd.DataFrame(rows)


def get_data(client: Client | None = None) -> pd.DataFrame:
    client = client or get_client()
    dim_df = fetch_table(client, "dim_games")
    metrics_df = fetch_table(client, "game_metrics")
    return pd.merge(dim_df, metrics_df, on="game_id", how="inner")


if __name__ == "__main__":
    df = get_data()
    print(df.head())
    print(len(df))
