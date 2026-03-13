from datetime import date, datetime

from app.database.supabase_client import supabase


def _validar_user_id(user_id):
    value = (user_id or "").strip() if isinstance(user_id, str) else user_id
    if not value:
        raise ValueError("user_id es obligatorio.")
    return value


def _validar_categoria(categoria: dict) -> dict:
    if not isinstance(categoria, dict):
        raise ValueError("categoria es obligatoria.")

    categoria_id = (categoria.get("id") or "").strip()
    categoria_nombre = (categoria.get("nombre") or "").strip()

    if not categoria_id:
        raise ValueError("categoria_id es obligatorio.")
    if not categoria_nombre:
        raise ValueError("nombre de categoria es obligatorio.")

    return {"id": categoria_id, "nombre": categoria_nombre}


def _normalizar_fecha(fecha):
    if not fecha:
        return date.today().isoformat()

    if isinstance(fecha, str) and fecha.lower() == "hoy":
        return date.today().isoformat()

    if isinstance(fecha, str):
        datetime.fromisoformat(fecha)
        return fecha

    raise ValueError("Fecha invalida. Debe estar en formato YYYY-MM-DD.")


def _normalizar_monto(monto):
    try:
        monto_num = float(monto)
    except (TypeError, ValueError):
        raise ValueError("Monto invalido. Debe ser numerico.")

    if monto_num <= 0:
        raise ValueError("Monto invalido. Debe ser mayor a 0.")

    return monto_num


def validar_movimiento_para_insert(movimiento: dict, user_id: str, categoria_resuelta: dict) -> dict:
    user_id_valido = _validar_user_id(user_id)
    categoria_valida = _validar_categoria(categoria_resuelta)

    tipo = movimiento.get("tipo")
    if tipo not in {"gasto", "ingreso"}:
        raise ValueError("Tipo invalido. Debe ser 'gasto' o 'ingreso'.")

    descripcion = (movimiento.get("descripcion") or "").strip()
    if not descripcion:
        raise ValueError("Descripcion obligatoria.")

    monto = _normalizar_monto(movimiento.get("monto"))

    fecha = _normalizar_fecha(movimiento.get("fecha"))

    return {
        "user_id": user_id_valido,
        "categoria_id": categoria_valida["id"],
        "tipo": tipo,
        "descripcion": descripcion,
        "monto": monto,
        # Se mantiene por compatibilidad mientras exista columna textual.
        "categoria": categoria_valida["nombre"],
        "fecha": fecha,
    }


def guardar_movimiento(movimiento: dict, user_id: str, categoria_resuelta: dict):
    data = validar_movimiento_para_insert(movimiento, user_id, categoria_resuelta)
    response = supabase.table("movimientos").insert(data).execute()
    return response, data


def obtener_movimientos_por_usuario(user_id: str, limit: int = 20):
    user_id_valido = _validar_user_id(user_id)
    limit_valido = max(1, min(int(limit), 100))

    response = (
        supabase.table("movimientos")
        .select("*")
        .eq("user_id", user_id_valido)
        .order("fecha", desc=True)
        .limit(limit_valido)
        .execute()
    )

    return response.data or []


def sum_movimientos_by_period(user_id: str, tipo: str, fecha_inicio: str, fecha_fin: str) -> float:
    user_id_valido = _validar_user_id(user_id)
    tipo_valido = (tipo or "").strip().lower()
    if tipo_valido not in {"gasto", "ingreso"}:
        raise ValueError("Tipo invalido para consulta. Debe ser 'gasto' o 'ingreso'.")

    response = (
        supabase.table("movimientos")
        .select("monto")
        .eq("user_id", user_id_valido)
        .eq("tipo", tipo_valido)
        .gte("fecha", fecha_inicio)
        .lte("fecha", fecha_fin)
        .execute()
    )

    data = response.data or []
    total = 0.0
    for row in data:
        monto = row.get("monto")
        try:
            total += float(monto)
        except (TypeError, ValueError):
            continue

    return total


def sum_movimientos_by_period_and_category(
    user_id: str, tipo: str, fecha_inicio: str, fecha_fin: str, categoria_id: str
) -> float:
    user_id_valido = _validar_user_id(user_id)
    tipo_valido = (tipo or "").strip().lower()
    categoria_id_valido = (categoria_id or "").strip()

    if tipo_valido not in {"gasto", "ingreso"}:
        raise ValueError("Tipo invalido para consulta. Debe ser 'gasto' o 'ingreso'.")
    if not categoria_id_valido:
        raise ValueError("categoria_id es obligatorio para consulta por categoria.")

    response = (
        supabase.table("movimientos")
        .select("monto")
        .eq("user_id", user_id_valido)
        .eq("tipo", tipo_valido)
        .eq("categoria_id", categoria_id_valido)
        .gte("fecha", fecha_inicio)
        .lte("fecha", fecha_fin)
        .execute()
    )

    data = response.data or []
    total = 0.0
    for row in data:
        monto = row.get("monto")
        try:
            total += float(monto)
        except (TypeError, ValueError):
            continue
    return total


def sum_movimientos_grouped_by_category(
    user_id: str, tipo: str, fecha_inicio: str, fecha_fin: str
) -> list[dict]:
    user_id_valido = _validar_user_id(user_id)
    tipo_valido = (tipo or "").strip().lower()
    if tipo_valido not in {"gasto", "ingreso"}:
        raise ValueError("Tipo invalido para desglose. Debe ser 'gasto' o 'ingreso'.")

    response = (
        supabase.table("movimientos")
        .select("monto,categoria_id")
        .eq("user_id", user_id_valido)
        .eq("tipo", tipo_valido)
        .gte("fecha", fecha_inicio)
        .lte("fecha", fecha_fin)
        .execute()
    )

    grouped: dict[str, float] = {}
    for row in response.data or []:
        categoria_id = (row.get("categoria_id") or "").strip() or "__sin_categoria__"
        try:
            monto = float(row.get("monto"))
        except (TypeError, ValueError):
            continue
        grouped[categoria_id] = grouped.get(categoria_id, 0.0) + monto

    return [
        {"categoria_id": categoria_id, "total": total}
        for categoria_id, total in sorted(grouped.items(), key=lambda x: x[1], reverse=True)
    ]
