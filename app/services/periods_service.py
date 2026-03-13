from datetime import date, timedelta


SUPPORTED_PERIODS = {
    "hoy",
    "ayer",
    "esta_semana",
    "semana_pasada",
    "este_mes",
    "mes_pasado",
    "ultimos_7_dias",
    "ultimos_30_dias",
}


def _first_day_of_month(d: date) -> date:
    return d.replace(day=1)


def _last_day_of_previous_month(d: date) -> date:
    return _first_day_of_month(d) - timedelta(days=1)


def resolve_period_to_range(periodo: str, today: date | None = None) -> tuple[str, str, str]:
    if not periodo:
        raise ValueError("Periodo vacio.")

    ref = today or date.today()
    p = periodo.strip().lower()

    if p not in SUPPORTED_PERIODS:
        raise ValueError(f"Periodo no soportado: {p}")

    if p == "hoy":
        start = end = ref
    elif p == "ayer":
        start = end = ref - timedelta(days=1)
    elif p == "esta_semana":
        start = ref - timedelta(days=ref.weekday())  # lunes
        end = ref
    elif p == "semana_pasada":
        this_monday = ref - timedelta(days=ref.weekday())
        start = this_monday - timedelta(days=7)
        end = this_monday - timedelta(days=1)  # domingo
    elif p == "este_mes":
        start = _first_day_of_month(ref)
        end = ref
    elif p == "mes_pasado":
        end = _last_day_of_previous_month(ref)
        start = _first_day_of_month(end)
    elif p == "ultimos_7_dias":
        start = ref - timedelta(days=6)
        end = ref
    else:  # ultimos_30_dias
        start = ref - timedelta(days=29)
        end = ref

    return start.isoformat(), end.isoformat(), p


def period_label(periodo: str) -> str:
    labels = {
        "hoy": "hoy",
        "ayer": "ayer",
        "esta_semana": "esta semana",
        "semana_pasada": "la semana pasada",
        "este_mes": "este mes",
        "mes_pasado": "el mes pasado",
        "ultimos_7_dias": "los ultimos 7 dias",
        "ultimos_30_dias": "los ultimos 30 dias",
    }
    return labels.get((periodo or "").strip().lower(), "ese periodo")
