from datetime import date, timedelta

from app.dashboard.queries.common import get_movimientos_between, get_user_categories, to_float


def get_category_filter_options(client, user_id: str) -> list[str]:
    categorias = get_user_categories(client, user_id)
    names = []
    for categoria in categorias:
        nombre = str(categoria.get("nombre") or "").strip()
        if nombre:
            names.append(nombre)
    return sorted(set(names))


def get_category_expense_summary(client, user_id: str, days: int = 30, visible_categories: list[str] | None = None) -> list[dict]:
    start_date = date.today() - timedelta(days=max(days - 1, 0))
    movimientos = get_movimientos_between(client, user_id, start_date=start_date, end_date=date.today())

    allowed = set(visible_categories or [])
    grouped: dict[str, dict] = {}

    for movimiento in movimientos:
        if (movimiento.get("tipo") or "").strip().lower() != "gasto":
            continue

        categoria = (movimiento.get("categoria") or "").strip() or "Sin categoria"
        if allowed and categoria not in allowed:
            continue

        monto = to_float(movimiento.get("monto"))

        if categoria not in grouped:
            grouped[categoria] = {
                "categoria": categoria,
                "total_gastado": 0.0,
                "cantidad_movimientos": 0,
            }

        grouped[categoria]["total_gastado"] += monto
        grouped[categoria]["cantidad_movimientos"] += 1

    return sorted(grouped.values(), key=lambda item: item["total_gastado"], reverse=True)
