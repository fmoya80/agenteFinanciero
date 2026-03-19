from pprint import pprint
import os

from dotenv import load_dotenv

from app.database.supabase_client import get_supabase_client


load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Falta {name} en el archivo .env.")
    return value


def print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def fetch_last_categories(supabase) -> list[dict]:
    try:
        response = (
            supabase.table("categorias")
            .select("*")
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
        return response.data or []
    except Exception:
        response = (
            supabase.table("categorias")
            .select("*")
            .limit(5)
            .execute()
        )
        return response.data or []


def main() -> None:
    email = require_env("SUPABASE_EMAIL")
    password = require_env("SUPABASE_PASSWORD")

    supabase = get_supabase_client()

    auth_response = supabase.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )

    session = auth_response.session
    user = auth_response.user

    if session is None or user is None:
        raise RuntimeError("No se pudo iniciar sesion en Supabase.")

    print_section("Usuario autenticado")
    pprint(
        {
            "id": user.id,
            "email": user.email,
            "role": getattr(user, "role", None),
        }
    )

    users_response = (
        supabase.table("users")
        .select("*")
        .order("id")
        .execute()
    )

    print_section("Filas visibles de public.users")
    pprint(users_response.data or [])

    movimientos_response = (
        supabase.table("movimientos")
        .select("*")
        .order("fecha", desc=True)
        .limit(5)
        .execute()
    )

    print_section("Ultimos 5 movimientos")
    pprint(movimientos_response.data or [])

    print_section("Ultimas 5 categorias")
    pprint(fetch_last_categories(supabase))


if __name__ == "__main__":
    main()
