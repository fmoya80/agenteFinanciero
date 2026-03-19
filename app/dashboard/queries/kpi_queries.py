from datetime import date, timedelta

from app.dashboard.queries.common import get_movimientos_between, to_date, to_float


def get_kpi_block_data(client, user_id: str) -> dict:
    today = date.today()
    current_30_start = today - timedelta(days=29)
    previous_30_start = current_30_start - timedelta(days=30)
    current_7_start = today - timedelta(days=6)
    previous_7_start = current_7_start - timedelta(days=7)

    movimientos = get_movimientos_between(client, user_id, start_date=previous_30_start, end_date=today)

    current_ingresos_30d = 0.0
    previous_ingresos_30d = 0.0
    current_gastos_30d = 0.0
    previous_gastos_30d = 0.0
    current_gasto_7d = 0.0
    previous_gasto_7d = 0.0

    for movimiento in movimientos:
        fecha = to_date(movimiento.get("fecha"))
        if not fecha:
            continue

        monto = to_float(movimiento.get("monto"))
        tipo = (movimiento.get("tipo") or "").strip().lower()

        if current_30_start <= fecha <= today:
            if tipo == "ingreso":
                current_ingresos_30d += monto
            elif tipo == "gasto":
                current_gastos_30d += monto

        if previous_30_start <= fecha < current_30_start:
            if tipo == "ingreso":
                previous_ingresos_30d += monto
            elif tipo == "gasto":
                previous_gastos_30d += monto

        if current_7_start <= fecha <= today and tipo == "gasto":
            current_gasto_7d += monto

        if previous_7_start <= fecha < current_7_start and tipo == "gasto":
            previous_gasto_7d += monto

    current_balance_30d = current_ingresos_30d - current_gastos_30d
    previous_balance_30d = previous_ingresos_30d - previous_gastos_30d

    return {
        "ingresos_30d": {
            "label": "Ingresos 30d",
            "value": current_ingresos_30d,
            "previous_value": previous_ingresos_30d,
            "delta": current_ingresos_30d - previous_ingresos_30d,
        },
        "gastos_30d": {
            "label": "Gastos 30d",
            "value": current_gastos_30d,
            "previous_value": previous_gastos_30d,
            "delta": current_gastos_30d - previous_gastos_30d,
        },
        "balance_30d": {
            "label": "Balance 30d",
            "value": current_balance_30d,
            "previous_value": previous_balance_30d,
            "delta": current_balance_30d - previous_balance_30d,
        },
        "gasto_7d": {
            "label": "Gasto 7d",
            "value": current_gasto_7d,
            "previous_value": previous_gasto_7d,
            "delta": current_gasto_7d - previous_gasto_7d,
        },
    }
