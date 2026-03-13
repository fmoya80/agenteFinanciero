from typing import Optional

from app.database.supabase_client import supabase


def _normalizar_phone_number(phone_number: str) -> str:
    if phone_number is None:
        raise ValueError("phone_number es obligatorio.")

    phone = str(phone_number).strip()
    if not phone:
        raise ValueError("phone_number es obligatorio.")

    return phone


def get_user_by_phone(phone_number: str) -> Optional[dict]:
    phone = _normalizar_phone_number(phone_number)

    response = (
        supabase.table("users")
        .select("id, phone_number, display_name")
        .eq("phone_number", phone)
        .limit(1)
        .execute()
    )

    data = response.data or []
    return data[0] if data else None


def create_user(phone_number: str, display_name: Optional[str] = None) -> dict:
    phone = _normalizar_phone_number(phone_number)
    clean_name = (display_name or "").strip() or None

    response = (
        supabase.table("users")
        .insert({"phone_number": phone, "display_name": clean_name})
        .execute()
    )

    data = response.data or []
    if not data:
        raise RuntimeError("No se pudo crear el usuario en Supabase.")

    return data[0]


def get_or_create_user(phone_number: str, display_name: Optional[str] = None) -> dict:
    user = get_user_by_phone(phone_number)
    if user:
        return user

    try:
        return create_user(phone_number, display_name)
    except Exception:
        # Evita condicion de carrera por constraint unique(phone_number)
        user = get_user_by_phone(phone_number)
        if user:
            return user
        raise
