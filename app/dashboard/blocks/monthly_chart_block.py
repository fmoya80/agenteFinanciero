import pandas as pd
import streamlit as st

from app.dashboard.queries.monthly_chart_queries import get_monthly_bar_chart_data


def render_monthly_chart_block(client, user_id: str) -> None:
    st.subheader("Bloque 2: Ingresos y gastos por mes")

    rows = get_monthly_bar_chart_data(client, user_id, months=6)
    if not rows:
        st.info("No hay datos suficientes para mostrar el grafico mensual.")
        return

    dataframe = pd.DataFrame(rows)
    dataframe = dataframe.set_index("month")[["ingresos", "gastos"]]

    st.bar_chart(dataframe, use_container_width=True)
