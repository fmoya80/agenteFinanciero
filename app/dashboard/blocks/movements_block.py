from datetime import date, timedelta

import pandas as pd
import streamlit as st

from app.dashboard.queries.movements_queries import get_movement_filter_options, get_operational_movimientos


def _prepare_dataframe(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    dataframe = pd.DataFrame(rows).copy()
    preferred_columns = ["fecha", "tipo", "descripcion", "categoria", "monto"]
    available_columns = [column for column in preferred_columns if column in dataframe.columns]
    if available_columns:
        dataframe = dataframe[available_columns]

    if "monto" in dataframe.columns:
        dataframe["monto"] = pd.to_numeric(dataframe["monto"], errors="coerce").fillna(0).round(2)

    return dataframe


def render_movements_block(client, user_id: str) -> None:
    st.subheader("Bloque 4: Detalle operativo")

    options = get_movement_filter_options(client, user_id)

    filter_col_1, filter_col_2, filter_col_3 = st.columns(3)
    with filter_col_1:
        search_text = st.text_input("Buscar descripcion", key="movements_search_text")
        selected_tipo = st.selectbox("Tipo", options=options["tipos"], key="movements_tipo")

    with filter_col_2:
        selected_categories = st.multiselect(
            "Categorias",
            options=options["categorias"],
            key="movements_categories",
        )

    with filter_col_3:
        default_start = date.today() - timedelta(days=30)
        start_date = st.date_input("Desde", value=default_start, key="movements_start_date")
        end_date = st.date_input("Hasta", value=date.today(), key="movements_end_date")

    if start_date > end_date:
        st.warning("La fecha 'Desde' no puede ser mayor que la fecha 'Hasta'.")
        return

    rows = get_operational_movimientos(
        client,
        user_id,
        search_text=search_text,
        categorias=selected_categories or None,
        tipo=selected_tipo,
        start_date=start_date,
        end_date=end_date,
        limit=200,
    )

    dataframe = _prepare_dataframe(rows)
    if dataframe.empty:
        st.info("No hay movimientos para los filtros seleccionados.")
        return

    st.dataframe(dataframe, use_container_width=True, hide_index=True)
