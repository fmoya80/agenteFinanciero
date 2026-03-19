import streamlit as st

from app.dashboard.auth import sign_out
from app.dashboard.blocks.category_block import render_category_block
from app.dashboard.blocks.kpis_block import render_kpis_block
from app.dashboard.blocks.monthly_chart_block import render_monthly_chart_block
from app.dashboard.blocks.movements_block import render_movements_block
from app.dashboard.queries.profile_queries import get_profile_header_data
from app.dashboard.ui_utils import get_display_name


def render_dashboard_page(client, auth_user: dict) -> None:
    profile_data = get_profile_header_data(client, auth_user["id"])
    user_profile = profile_data["user_profile"]
    display_name = get_display_name(auth_user, user_profile)

    st.title("Dashboard financiero")
    st.caption("Version 0.1 modular: cada bloque vive en su propio archivo.")

    with st.sidebar:
        st.subheader("Sesion")
        st.write(auth_user["email"])
        if st.button("Cerrar sesion", use_container_width=True):
            sign_out()
            st.rerun()

        with st.expander("Perfil del usuario"):
            if user_profile:
                st.json(user_profile)
            else:
                st.info("No se encontro perfil visible en public.users.")

    st.subheader(f"Hola, {display_name}")
    st.caption("Puedes iterar cada bloque por separado sin tocar toda la pagina.")

    render_kpis_block(client, auth_user["id"])
    st.divider()
    render_monthly_chart_block(client, auth_user["id"])
    st.divider()
    render_category_block(client, auth_user["id"])
    st.divider()
    render_movements_block(client, auth_user["id"])
