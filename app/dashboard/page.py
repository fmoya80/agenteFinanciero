from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from app.dashboard.auth import sign_out
from app.dashboard.queries.common import get_movimientos_between, get_user_categories, to_date, to_float
from app.dashboard.queries.profile_queries import get_profile_header_data
from app.dashboard.ui_utils import format_currency, get_display_name


TIME_FILTER_OPTIONS = [
    "Ultimos 30 dias",
    "Ultimos 7 dias",
    "Ultimos 90 dias",
    "Mes actual",
    "Mes anterior",
    "Rango personalizado",
]

CLP_AXIS_LABEL_EXPR = "'$ ' + replace(format(datum.value, ',.0f'), ',', '.')"
CATEGORY_FILTER_KEY = "dashboard_category_filter"
CATEGORY_FILTER_OPTIONS_KEY = "dashboard_category_filter_options"
BAR_LABEL_MIN_SHARE = 0.22
SUMMARY_MONTH_FORMAT = "%b-%Y"


def _month_start(value: date) -> date:
    return value.replace(day=1)


def _previous_month_range(today: date) -> tuple[date, date]:
    current_month_start = _month_start(today)
    previous_month_end = current_month_start - timedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1)
    return previous_month_start, previous_month_end


def _next_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def resolve_time_range(option: str) -> tuple[date, date]:
    today = date.today()

    if option == "Ultimos 7 dias":
        return today - timedelta(days=6), today
    if option == "Ultimos 90 dias":
        return today - timedelta(days=89), today
    if option == "Mes actual":
        return _month_start(today), today
    if option == "Mes anterior":
        return _previous_month_range(today)

    return today - timedelta(days=29), today


def load_filtered_data(client, user_id: str, start_date: date, end_date: date) -> dict:
    return {
        "movimientos": get_movimientos_between(
            client,
            user_id,
            start_date=start_date,
            end_date=end_date,
            order_desc=True,
            limit=5000,
        ),
        "categorias": get_user_categories(client, user_id),
    }


def load_summary_data(client, user_id: str) -> list[dict]:
    today = date.today()
    return get_movimientos_between(
        client,
        user_id,
        end_date=today,
        order_desc=False,
        limit=20000,
    )


def apply_global_filters(movimientos: list[dict], selected_categories: list[str] | None = None) -> list[dict]:
    if selected_categories is None:
        return movimientos
    allowed_categories = set(selected_categories)

    filtered_rows = []
    for movimiento in movimientos:
        categoria = (movimiento.get("categoria") or "").strip() or "Sin categoria"
        if categoria in allowed_categories:
            filtered_rows.append(movimiento)

    return filtered_rows


def apply_dashboard_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: #FFFFFF;
        }

        [data-testid="stHeader"] {
            background: rgba(255, 255, 255, 0.92);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #4D658D 0%, #435A80 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.10);
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p {
            color: #F8FAFC;
        }

        [data-testid="stSidebar"] .stButton > button {
            background: #F8FAFC;
            color: #1E293B;
            border: 1px solid rgba(30, 41, 59, 0.22);
            font-weight: 600;
        }

        [data-testid="stSidebar"] .stButton > button:hover {
            background: #E2E8F0;
            color: #0F172A;
            border-color: rgba(15, 23, 42, 0.28);
        }

        [data-testid="stSidebar"] .stButton > button:focus {
            box-shadow: 0 0 0 0.2rem rgba(255, 255, 255, 0.18);
        }

        [data-testid="stSidebar"] div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] .stDateInput input {
            background: rgba(255, 255, 255, 0.98);
            color: #0F172A;
            caret-color: #0F172A;
            border-color: rgba(15, 23, 42, 0.14);
        }

        [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
            background: rgba(255, 255, 255, 0.22);
            color: #FFFFFF;
        }

        [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] span,
        [data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] svg,
        [data-testid="stSidebar"] [data-baseweb="select"] input,
        [data-testid="stSidebar"] [data-baseweb="select"] div,
        [data-testid="stSidebar"] .stDateInput input::placeholder {
            color: #0F172A;
            fill: #0F172A;
        }

        div[data-baseweb="popover"] [role="listbox"] {
            background: #FFFFFF;
            color: #0F172A;
        }

        div[data-baseweb="popover"] [role="option"] {
            background: #FFFFFF;
            color: #0F172A;
        }

        div[data-baseweb="popover"] [role="option"][aria-selected="true"] {
            background: #E8EEF8;
            color: #0F172A;
        }

        div[data-baseweb="popover"] [role="option"]:hover {
            background: #EEF4FF;
        }

        [data-testid="stSidebar"] hr {
            margin-top: 0.7rem;
            margin-bottom: 0.65rem;
            border-color: rgba(255, 255, 255, 0.18);
        }

        .sidebar-session-email {
            margin: 0.15rem 0 0.6rem 0;
            padding: 0.45rem 0.65rem;
            border-radius: 0.65rem;
            background: rgba(255, 255, 255, 0.16);
            color: #FFFFFF;
            font-size: 0.95rem;
            line-height: 1.35;
            word-break: break-word;
        }

        .sidebar-section-title {
            margin: 0.1rem 0 0.1rem 0;
            color: #FFFFFF;
            font-weight: 600;
            font-size: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_category_options(categorias: list[dict], movimientos: list[dict]) -> list[str]:
    names = set()

    for categoria in categorias:
        nombre = str(categoria.get("nombre") or "").strip()
        if nombre:
            names.add(nombre)

    for movimiento in movimientos:
        nombre = str(movimiento.get("categoria") or "").strip() or "Sin categoria"
        if nombre:
            names.add(nombre)

    return sorted(names)


def filter_rows_by_date(movimientos: list[dict], start_date: date, end_date: date) -> list[dict]:
    filtered_rows = []

    for movimiento in movimientos:
        fecha = to_date(movimiento.get("fecha"))
        if not fecha:
            continue
        if start_date <= fecha <= end_date:
            filtered_rows.append(movimiento)

    return filtered_rows


def sum_amount_by_type(movimientos: list[dict], tipo: str | None = None) -> float:
    total = 0.0

    for movimiento in movimientos:
        current_type = (movimiento.get("tipo") or "").strip().lower()
        if tipo and current_type != tipo:
            continue
        total += to_float(movimiento.get("monto"))

    return total


def get_previous_period_comparison(current_value: float, previous_value: float) -> dict:
    if previous_value == 0:
        if current_value == 0:
            change_pct = 0.0
        else:
            change_pct = 100.0
    else:
        change_pct = ((current_value - previous_value) / abs(previous_value)) * 100

    return {
        "previous_value": previous_value,
        "delta_pct": change_pct,
        "delta_label": f"{change_pct:+.1f}% vs periodo anterior",
    }


def get_summary_metrics(movimientos: list[dict]) -> list[dict]:
    today = date.today()
    current_30_start = today - timedelta(days=29)
    previous_30_start = current_30_start - timedelta(days=30)
    previous_30_end = current_30_start - timedelta(days=1)
    current_7_start = today - timedelta(days=6)
    previous_7_start = current_7_start - timedelta(days=7)
    previous_7_end = current_7_start - timedelta(days=1)

    current_30_rows = filter_rows_by_date(movimientos, current_30_start, today)
    previous_30_rows = filter_rows_by_date(movimientos, previous_30_start, previous_30_end)
    current_7_rows = filter_rows_by_date(movimientos, current_7_start, today)
    previous_7_rows = filter_rows_by_date(movimientos, previous_7_start, previous_7_end)

    current_ingresos_30d = sum_amount_by_type(current_30_rows, "ingreso")
    previous_ingresos_30d = sum_amount_by_type(previous_30_rows, "ingreso")
    current_gastos_30d = sum_amount_by_type(current_30_rows, "gasto")
    previous_gastos_30d = sum_amount_by_type(previous_30_rows, "gasto")
    current_balance_30d = current_ingresos_30d - current_gastos_30d
    previous_balance_30d = previous_ingresos_30d - previous_gastos_30d
    current_gastos_7d = sum_amount_by_type(current_7_rows, "gasto")
    previous_gastos_7d = sum_amount_by_type(previous_7_rows, "gasto")
    current_movimientos_30d = float(len(current_30_rows))
    previous_movimientos_30d = float(len(previous_30_rows))

    metrics = [
        {
            "label": "Gastos 7 dias",
            "value": current_gastos_7d,
            "comparison": get_previous_period_comparison(current_gastos_7d, previous_gastos_7d),
            "delta_color": "inverse",
            "help": "Comparado contra los 7 dias anteriores.",
        },
        {
            "label": "Ingresos 30 dias",
            "value": current_ingresos_30d,
            "comparison": get_previous_period_comparison(current_ingresos_30d, previous_ingresos_30d),
            "delta_color": "normal",
            "help": "Comparado contra los 30 dias anteriores.",
        },
        {
            "label": "Gastos 30 dias",
            "value": current_gastos_30d,
            "comparison": get_previous_period_comparison(current_gastos_30d, previous_gastos_30d),
            "delta_color": "inverse",
            "help": "Comparado contra los 30 dias anteriores.",
        },
        {
            "label": "Balance 30 dias",
            "value": current_balance_30d,
            "comparison": get_previous_period_comparison(current_balance_30d, previous_balance_30d),
            "delta_color": "normal",
            "help": "Comparado contra los 30 dias anteriores.",
        },
        {
            "label": "Movimientos 30 dias",
            "value": current_movimientos_30d,
            "comparison": get_previous_period_comparison(current_movimientos_30d, previous_movimientos_30d),
            "delta_color": "normal",
            "help": "Cantidad de movimientos respecto a los 30 dias anteriores.",
            "is_count": True,
        },
    ]

    return metrics


def build_monthly_chart_dataframe(movimientos: list[dict]) -> pd.DataFrame:
    dated_rows = []

    for movimiento in movimientos:
        fecha = to_date(movimiento.get("fecha"))
        if not fecha:
            continue

        dated_rows.append((fecha, movimiento))

    if not dated_rows:
        return pd.DataFrame()

    first_month = _month_start(min(fecha for fecha, _ in dated_rows))
    last_month = _month_start(date.today())
    grouped: dict[str, dict] = {}
    current_month = first_month

    while current_month <= last_month:
        key = current_month.isoformat()
        grouped[key] = {
            "month_date": current_month,
            "month_label": current_month.strftime(SUMMARY_MONTH_FORMAT),
            "Ingresos": 0.0,
            "Gastos": 0.0,
        }
        current_month = _next_month(current_month)

    for fecha, movimiento in dated_rows:
        key = fecha.replace(day=1).isoformat()
        if key not in grouped:
            continue

        monto = to_float(movimiento.get("monto"))
        tipo = (movimiento.get("tipo") or "").strip().lower()

        if tipo == "ingreso":
            grouped[key]["Ingresos"] += monto
        elif tipo == "gasto":
            grouped[key]["Gastos"] += monto

    return pd.DataFrame(grouped.values())


def build_category_summary_dataframe(movimientos: list[dict]) -> pd.DataFrame:
    rows: list[dict] = []

    for movimiento in movimientos:
        if (movimiento.get("tipo") or "").strip().lower() != "gasto":
            continue

        rows.append(
            {
                "categoria": (movimiento.get("categoria") or "").strip() or "Sin categoria",
                "monto": to_float(movimiento.get("monto")),
            }
        )

    if not rows:
        return pd.DataFrame()

    dataframe = pd.DataFrame(rows)
    summary = (
        dataframe.groupby("categoria", dropna=False)["monto"]
        .agg(total_gastado="sum", cantidad_movimientos="count")
        .reset_index()
        .sort_values("total_gastado", ascending=False)
    )

    total = float(summary["total_gastado"].sum())
    max_total = float(summary["total_gastado"].max()) if not summary.empty else 0.0
    summary["porcentaje"] = summary["total_gastado"].apply(lambda value: (value / total * 100) if total else 0.0)
    summary["share_of_max"] = summary["total_gastado"].apply(lambda value: (value / max_total) if max_total else 0.0)
    summary["total_gastado"] = summary["total_gastado"].round(2)
    summary["total_gastado_label"] = summary["total_gastado"].apply(format_currency)
    summary["porcentaje_label"] = summary["porcentaje"].apply(lambda value: f"{value:.1f}%")
    summary["bar_label"] = summary.apply(
        lambda row: row["total_gastado_label"] if row["share_of_max"] >= BAR_LABEL_MIN_SHARE else "",
        axis=1,
    )
    return summary


def build_detail_dataframe(movimientos: list[dict]) -> pd.DataFrame:
    if not movimientos:
        return pd.DataFrame()

    dataframe = pd.DataFrame(movimientos).copy()
    preferred_columns = ["fecha", "tipo", "descripcion", "categoria", "monto"]
    available_columns = [column for column in preferred_columns if column in dataframe.columns]

    if available_columns:
        dataframe = dataframe[available_columns]

    if "monto" in dataframe.columns:
        dataframe["monto"] = pd.to_numeric(dataframe["monto"], errors="coerce").fillna(0).round(2)
        dataframe["monto"] = dataframe["monto"].apply(format_currency)

    return dataframe.sort_values("fecha", ascending=False)


def build_summary_chart(movimientos: list[dict]) -> alt.Chart:
    dataframe = build_monthly_chart_dataframe(movimientos)
    if dataframe.empty:
        return None

    chart_df = dataframe.melt(
        id_vars=["month_date", "month_label"],
        value_vars=["Ingresos", "Gastos"],
        var_name="tipo",
        value_name="monto",
    )
    chart_df["monto_label"] = chart_df["monto"].apply(format_currency)

    return (
        alt.Chart(chart_df)
        .mark_bar(size=24, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(
                "month_label:N",
                title="Mes",
                sort=alt.SortField(field="month_date", order="ascending"),
                axis=alt.Axis(labelAngle=0),
                scale=alt.Scale(paddingInner=0.35, paddingOuter=0.2),
            ),
            xOffset=alt.XOffset("tipo:N"),
            y=alt.Y(
                "monto:Q",
                title="Monto",
                axis=alt.Axis(labelExpr=CLP_AXIS_LABEL_EXPR),
            ),
            color=alt.Color(
                "tipo:N",
                title="Tipo",
                scale=alt.Scale(domain=["Ingresos", "Gastos"], range=["#2E8B57", "#D1495B"]),
            ),
            tooltip=[
                alt.Tooltip("month_label:N", title="Mes"),
                alt.Tooltip("tipo:N", title="Tipo"),
                alt.Tooltip("monto_label:N", title="Monto"),
            ],
        )
        .properties(height=320)
    )


def build_category_bar_chart(summary_df: pd.DataFrame) -> alt.Chart:
    bars = (
        alt.Chart(summary_df)
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            x=alt.X(
                "total_gastado:Q",
                title="Total gastado",
                axis=alt.Axis(labelExpr=CLP_AXIS_LABEL_EXPR),
            ),
            y=alt.Y("categoria:N", title=None, sort="-x"),
            color=alt.value("#D1495B"),
            tooltip=[
                alt.Tooltip("categoria:N", title="Categoria"),
                alt.Tooltip("total_gastado_label:N", title="Total gastado"),
                alt.Tooltip("porcentaje_label:N", title="% del total"),
                alt.Tooltip("cantidad_movimientos:Q", title="Movimientos"),
            ],
        )
        .properties(height=max(280, 36 * len(summary_df)))
    )

    labels = (
        alt.Chart(summary_df[summary_df["bar_label"] != ""])
        .mark_text(align="right", baseline="middle", dx=-8, color="white", fontWeight="bold")
        .encode(
            x=alt.X("total_gastado:Q"),
            y=alt.Y("categoria:N", sort="-x"),
            text=alt.Text("bar_label:N"),
        )
    )

    return bars + labels


def build_category_pie_chart(summary_df: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(summary_df)
        .mark_arc(innerRadius=55)
        .encode(
            theta=alt.Theta("total_gastado:Q", title="Total gastado"),
            color=alt.Color("categoria:N", title="Categoria"),
            tooltip=[
                alt.Tooltip("categoria:N", title="Categoria"),
                alt.Tooltip("total_gastado_label:N", title="Total gastado"),
                alt.Tooltip("porcentaje_label:N", title="% del total"),
                alt.Tooltip("cantidad_movimientos:Q", title="Movimientos"),
            ],
        )
        .properties(height=320)
    )


def render_session_sidebar(auth_user: dict, user_profile: dict | None) -> None:
    with st.sidebar:
        st.subheader("Sesion")
        st.markdown(
            f'<div class="sidebar-session-email">{auth_user["email"]}</div>',
            unsafe_allow_html=True,
        )
        if st.button("Cerrar sesion", use_container_width=True):
            sign_out()
            st.rerun()

        with st.expander("Perfil del usuario"):
            if user_profile:
                st.json(user_profile)
            else:
                st.info("No se encontro perfil visible en public.users.")

        st.divider()
        st.markdown('<div class="sidebar-section-title">Filtros globales</div>', unsafe_allow_html=True)
        st.caption("Aplican a Categorias y Detalle. Resumen usa ventanas fijas de 7 y 30 dias.")


def render_time_filters() -> tuple[date, date]:
    with st.sidebar:
        selected_time_option = st.selectbox(
            "Periodo",
            options=TIME_FILTER_OPTIONS,
            index=0,
            help="Este filtro afecta las pestanas de Categorias y Detalle.",
        )

        if selected_time_option == "Rango personalizado":
            default_start = date.today() - timedelta(days=29)
            start_date = st.date_input("Desde", value=default_start)
            end_date = st.date_input("Hasta", value=date.today())
        else:
            start_date, end_date = resolve_time_range(selected_time_option)
            st.caption(f"Mostrando desde {start_date.isoformat()} hasta {end_date.isoformat()}.")

        if start_date > end_date:
            st.error("La fecha 'Desde' no puede ser mayor que la fecha 'Hasta'.")
            st.stop()

    return start_date, end_date


def render_category_filter(category_options: list[str]) -> list[str]:
    previous_options = st.session_state.get(CATEGORY_FILTER_OPTIONS_KEY)

    if CATEGORY_FILTER_KEY not in st.session_state:
        st.session_state[CATEGORY_FILTER_KEY] = list(category_options)
    else:
        selected_categories = [
            category for category in st.session_state[CATEGORY_FILTER_KEY] if category in category_options
        ]
        previous_options_set = set(previous_options or [])

        for category in category_options:
            if category not in previous_options_set and category not in selected_categories:
                selected_categories.append(category)

        st.session_state[CATEGORY_FILTER_KEY] = selected_categories

    st.session_state[CATEGORY_FILTER_OPTIONS_KEY] = list(category_options)

    with st.sidebar:
        return st.multiselect(
            "Categorias",
            options=category_options,
            key=CATEGORY_FILTER_KEY,
            help="Todas vienen seleccionadas por defecto; desmarca las que no quieras ver.",
        )


def render_summary_tab(summary_movimientos: list[dict]) -> None:
    st.caption(
        "KPIs calculados con ventanas fijas: 7 dias y 30 dias, independientes del filtro de fechas."
    )

    metrics = get_summary_metrics(summary_movimientos)
    columns = st.columns(len(metrics))

    for column, metric in zip(columns, metrics):
        value = metric["value"]
        display_value = str(int(value)) if metric.get("is_count") else format_currency(value)
        comparison = metric["comparison"]
        column.metric(
            metric["label"],
            display_value,
            delta=comparison["delta_label"],
            delta_color=metric["delta_color"],
            help=metric["help"],
        )

    st.markdown("### Evolucion mensual")
    st.caption("El grafico recorre toda la historia disponible del usuario, desde el primer mes con datos.")
    summary_chart = build_summary_chart(summary_movimientos)

    if summary_chart is None:
        st.info("No hay datos suficientes para mostrar el grafico mensual.")
        return

    st.altair_chart(summary_chart, use_container_width=True)


def render_categories_tab(movimientos: list[dict], start_date: date, end_date: date) -> None:
    st.caption(
        f"Distribucion de gastos por categoria desde {start_date.isoformat()} hasta {end_date.isoformat()}."
    )

    summary_df = build_category_summary_dataframe(movimientos)
    if summary_df.empty:
        st.info("No hay gastos para las categorias y fechas seleccionadas.")
        return

    bar_col, pie_col = st.columns([1.4, 1])

    with bar_col:
        st.altair_chart(build_category_bar_chart(summary_df), use_container_width=True)

    with pie_col:
        st.altair_chart(build_category_pie_chart(summary_df), use_container_width=True)


def render_detail_tab(movimientos: list[dict]) -> None:
    st.caption("Detalle de movimientos con los filtros globales aplicados.")

    detail_df = build_detail_dataframe(movimientos)
    if detail_df.empty:
        st.info("No hay movimientos para mostrar en este rango.")
        return

    st.dataframe(detail_df, use_container_width=True, hide_index=True)


def render_dashboard_page(client, auth_user: dict) -> None:
    apply_dashboard_styles()

    profile_data = get_profile_header_data(client, auth_user["id"])
    user_profile = profile_data["user_profile"]
    display_name = get_display_name(auth_user, user_profile)

    render_session_sidebar(auth_user, user_profile)
    start_date, end_date = render_time_filters()

    filtered_data = load_filtered_data(client, auth_user["id"], start_date, end_date)
    summary_movimientos = load_summary_data(client, auth_user["id"])

    category_options = get_category_options(filtered_data["categorias"], filtered_data["movimientos"])
    selected_categories = render_category_filter(category_options)
    movimientos_filtrados = apply_global_filters(filtered_data["movimientos"], selected_categories)

    st.title("Dashboard financiero")
    st.caption("Vista reorganizada con filtros globales, comparaciones de periodo y navegacion por pestanas.")
    st.subheader(f"Hola, {display_name}")

    total_gastado = sum_amount_by_type(movimientos_filtrados, "gasto")
    st.caption(
        f"{len(movimientos_filtrados)} movimientos visibles en el periodo filtrado. "
        f"Gasto acumulado: {format_currency(total_gastado)}."
    )

    summary_tab, categories_tab, detail_tab = st.tabs(
        ["\U0001F4CA Resumen", "\U0001F967 Categorias", "\U0001F4CB Detalle"]
    )

    with summary_tab:
        render_summary_tab(summary_movimientos)

    with categories_tab:
        render_categories_tab(movimientos_filtrados, start_date, end_date)

    with detail_tab:
        render_detail_tab(movimientos_filtrados)
