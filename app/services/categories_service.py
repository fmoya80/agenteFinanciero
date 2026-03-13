from typing import Optional

from app.database.supabase_client import supabase


def _normalizar_user_id(user_id: str) -> str:
    if user_id is None:
        raise ValueError("user_id es obligatorio.")
    value = str(user_id).strip()
    if not value:
        raise ValueError("user_id es obligatorio.")
    return value


def _normalizar_nombre_categoria(nombre: str) -> str:
    if nombre is None:
        raise ValueError("nombre de categoria es obligatorio.")
    value = str(nombre).strip()
    if not value:
        raise ValueError("nombre de categoria es obligatorio.")
    return value


def get_user_categories(user_id: str) -> list[dict]:
    user_id_valido = _normalizar_user_id(user_id)
    response = (
        supabase.table("categorias")
        .select("id, user_id, nombre, descripcion")
        .eq("user_id", user_id_valido)
        .order("nombre")
        .execute()
    )
    return response.data or []


def create_category(user_id: str, nombre: str, descripcion: Optional[str] = None) -> Optional[dict]:
    user_id_valido = _normalizar_user_id(user_id)
    nombre_valido = _normalizar_nombre_categoria(nombre)
    descripcion_limpia = (descripcion or "").strip() or None

    payload = {
        "user_id": user_id_valido,
        "nombre": nombre_valido,
        "descripcion": descripcion_limpia,
    }
    print("create_category payload:", payload)

    try:
        response = supabase.table("categorias").insert(payload).execute()
        data = response.data or []
        print("create_category response data:", data)
        if not data:
            print("create_category: insert sin filas retornadas")
            return None
        return data[0]
    except Exception as e:
        print("create_category error:", e)
        raise


def get_or_create_default_category(user_id: str) -> dict:
    user_id_valido = _normalizar_user_id(user_id)
    categorias = get_user_categories(user_id_valido)
    for categoria in categorias:
        if (categoria.get("nombre") or "").strip().lower() == "otros":
            return categoria

    try:
        created = create_category(user_id_valido, "otros", "Categoria por defecto")
        if created:
            return created
    except Exception:
        pass

    categorias = get_user_categories(user_id_valido)
    for categoria in categorias:
        if (categoria.get("nombre") or "").strip().lower() == "otros":
            return categoria
    raise RuntimeError("No se pudo asegurar la categoria por defecto 'otros'.")


def resolve_category_for_user(
    user_id: str, descripcion_movimiento: str, categorias_disponibles: list[dict], categoria_sugerida: Optional[str] = None
) -> dict:
    user_id_valido = _normalizar_user_id(user_id)
    categorias = list(categorias_disponibles or [])
    if not categorias:
        categorias = get_user_categories(user_id_valido)

    default_cat = None
    normalized_map = {}
    for categoria in categorias:
        nombre = (categoria.get("nombre") or "").strip()
        if not nombre:
            continue
        normalized_map[nombre.lower()] = categoria
        if nombre.lower() == "otros":
            default_cat = categoria

    if default_cat is None:
        default_cat = get_or_create_default_category(user_id_valido)
        normalized_map["otros"] = default_cat

    sugerida = (categoria_sugerida or "").strip().lower()
    if sugerida and sugerida in normalized_map:
        return normalized_map[sugerida]

    descripcion = (descripcion_movimiento or "").strip().lower()
    if descripcion:
        for nombre_norm, categoria in normalized_map.items():
            if nombre_norm != "otros" and nombre_norm in descripcion:
                return categoria

    return default_cat


def find_user_category_by_name(user_id: str, categoria_query: str, categorias_disponibles: list[dict] | None = None) -> Optional[dict]:
    user_id_valido = _normalizar_user_id(user_id)
    query = (categoria_query or "").strip().lower()
    if not query:
        return None

    categorias = list(categorias_disponibles or [])
    if not categorias:
        categorias = get_user_categories(user_id_valido)

    exact_match = None
    contains_match = None
    for categoria in categorias:
        nombre = (categoria.get("nombre") or "").strip()
        if not nombre:
            continue
        nombre_norm = nombre.lower()
        if nombre_norm == query:
            exact_match = categoria
            break
        if query in nombre_norm or nombre_norm in query:
            contains_match = contains_match or categoria

    return exact_match or contains_match
