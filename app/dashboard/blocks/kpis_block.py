import streamlit as st

from app.dashboard.queries.kpi_queries import get_kpi_block_data
from app.dashboard.ui_utils import format_currency, format_delta


def render_kpis_block(client, user_id: str) -> None:
    st.subheader("Bloque 1: KPIs")

    kpis = get_kpi_block_data(client, user_id)
    metric_keys = ["ingresos_30d", "gastos_30d", "balance_30d", "gasto_7d"]
    columns = st.columns(len(metric_keys))

    for column, key in zip(columns, metric_keys):
        metric = kpis[key]
        column.metric(
            metric["label"],
            format_currency(metric["value"]),
            delta=format_delta(metric["delta"]),
        )
