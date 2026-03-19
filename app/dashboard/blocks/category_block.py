import pandas as pd
import streamlit as st

from app.dashboard.queries.category_queries import get_category_expense_summary, get_category_filter_options


TIME_HORIZONS = {
    "7 dias": 7,
    "30 dias": 30,
    "90 dias": 90,
    "365 dias": 365,
}


def render_category_block(client, user_id: str) -> None:
    st.subheader("Bloque 3: Gasto por categoria")

    all_categories = get_category_filter_options(client, user_id)

    controls_col_1, controls_col_2 = st.columns([1, 2])
    with controls_col_1:
        horizon_label = st.selectbox(
            "Horizonte",
            options=list(TIME_HORIZONS.keys()),
            index=1,
            key="category_block_horizon",
        )

    with controls_col_2:
        visible_categories = st.multiselect(
            "Categorias visibles",
            options=all_categories,
            default=all_categories,
            key="category_block_visible_categories",
        )

    rows = get_category_expense_summary(
        client,
        user_id,
        days=TIME_HORIZONS[horizon_label],
        visible_categories=visible_categories or None,
    )

    if not rows:
        st.info("No hay gastos para las categorias seleccionadas.")
        return

    dataframe = pd.DataFrame(rows)
    chart_df = dataframe.set_index("categoria")[["total_gastado"]]

    chart_col, table_col = st.columns([1, 1])
    with chart_col:
        st.bar_chart(chart_df, use_container_width=True)

    with table_col:
        st.dataframe(dataframe, use_container_width=True, hide_index=True)
