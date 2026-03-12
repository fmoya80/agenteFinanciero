from supabase import create_client
import os

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print("URL:", url)
print("KEY:", key[:10] if key else None)

supabase = create_client(url, key)

try:
    test = supabase.table("movimientos").select("*").limit(1).execute()
    print("✅ Conexión a Supabase OK")
except Exception as e:
    print("❌ Error conectando a Supabase:", e)