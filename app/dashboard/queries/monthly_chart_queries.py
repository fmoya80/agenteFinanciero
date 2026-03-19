from datetime import date

from app.dashboard.queries.common import get_movimientos_between, to_date, to_float


def _month_start(year: int, month: int) -> date:
    return date(year, month, 1)


def _subtract_months(base: date, months: int) -> date:
    year = base.year
    month = base.month - months

    while month <= 0:
        month += 12
        year -= 1

    return _month_start(year, month)


def get_monthly_bar_chart_data(client, user_id: str, months: int = 6) -> list[dict]:
    today = date.today()
    this_month = _month_start(today.year, today.month)
    first_month = _subtract_months(this_month, months - 1)

    movimientos = get_movimientos_between(client, user_id, start_date=first_month, end_date=today)

    grouped: dict[str, dict] = {}
    for offset in range(months):
        month_date = _subtract_months(this_month, months - 1 - offset)
        key = month_date.strftime("%Y-%m")
        grouped[key] = {
            "month": key,
            "ingresos": 0.0,
            "gastos": 0.0,
        }

    for movimiento in movimientos:
        fecha = to_date(movimiento.get("fecha"))
        if not fecha:
            continue

        key = fecha.strftime("%Y-%m")
        if key not in grouped:
            continue

        monto = to_float(movimiento.get("monto"))
        tipo = (movimiento.get("tipo") or "").strip().lower()

        if tipo == "ingreso":
            grouped[key]["ingresos"] += monto
        elif tipo == "gasto":
            grouped[key]["gastos"] += monto

    return list(grouped.values())
