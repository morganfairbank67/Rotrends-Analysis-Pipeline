import os

from dotenv import find_dotenv, load_dotenv
from supabase import Client, create_client

load_dotenv(find_dotenv())


def get_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")
    return create_client(url, key)
