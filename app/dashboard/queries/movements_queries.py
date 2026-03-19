from datetime import date

from app.dashboard.queries.common import get_user_categories


def get_movement_filter_options(client, user_id: str) -> dict:
    categorias = []
    for categoria in get_user_categories(client, user_id):
        nombre = str(categoria.get("nombre") or "").strip()
        if nombre:
            categorias.append(nombre)

    return {
        "categorias": sorted(set(categorias)),
        "tipos": ["todos", "gasto", "ingreso"],
    }


def get_operational_movimientos(
    client,
    user_id: str,
    *,
    search_text: str = "",
    categorias: list[str] | None = None,
    tipo: str = "todos",
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 200,
) -> list[dict]:
    query = client.table("movimientos").select("*").eq("user_id", user_id)

    clean_search = search_text.strip()
    if clean_search:
        query = query.ilike("descripcion", f"%{clean_search}%")

    if categorias:
        query = query.in_("categoria", categorias)

    clean_tipo = (tipo or "").strip().lower()
    if clean_tipo in {"gasto", "ingreso"}:
        query = query.eq("tipo", clean_tipo)

    if start_date:
        query = query.gte("fecha", start_date.isoformat())

    if end_date:
        query = query.lte("fecha", end_date.isoformat())

    response = query.order("fecha", desc=True).limit(limit).execute()
    return response.data or []
