from datetime import date, datetime


def to_float(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def to_date(value) -> date | None:
    if not value:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


def get_user_profile(client, user_id: str) -> dict | None:
    response = (
        client.table("users")
        .select("*")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    data = response.data or []
    return data[0] if data else None


def get_user_categories(client, user_id: str) -> list[dict]:
    try:
        response = (
            client.table("categorias")
            .select("*")
            .eq("user_id", user_id)
            .order("nombre")
            .execute()
        )
        return response.data or []
    except Exception:
        response = (
            client.table("categorias")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        return response.data or []


def get_movimientos_between(
    client,
    user_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    *,
    order_desc: bool = False,
    limit: int | None = None,
) -> list[dict]:
    query = client.table("movimientos").select("*").eq("user_id", user_id)

    if start_date:
        query = query.gte("fecha", start_date.isoformat())
    if end_date:
        query = query.lte("fecha", end_date.isoformat())

    query = query.order("fecha", desc=order_desc)

    if limit is not None:
        query = query.limit(limit)

    response = query.execute()
    return response.data or []
