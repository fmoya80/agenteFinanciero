from supabase import create_client
import os

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_KEY en variables de entorno.")

supabase = create_client(url, key)
