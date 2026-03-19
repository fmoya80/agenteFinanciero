import os

from dotenv import load_dotenv
from supabase import Client, create_client


load_dotenv()


def get_supabase_url() -> str:
    return os.getenv("SUPABASE_URL", "").strip()


def get_supabase_anon_key() -> str:
    return (os.getenv("SUPABASE_ANON_KEY", "").strip() or os.getenv("SUPABASE_KEY", "").strip())


def get_supabase_client(url: str | None = None, key: str | None = None) -> Client:
    url = (url or get_supabase_url()).strip()
    key = (key or get_supabase_anon_key()).strip()

    if not url:
        raise RuntimeError("Falta SUPABASE_URL en el archivo .env.")

    if not key:
        raise RuntimeError("Falta SUPABASE_ANON_KEY en el archivo .env.")

    return create_client(url, key)


supabase = get_supabase_client()
