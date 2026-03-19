import os

from dotenv import load_dotenv
import streamlit as st

from app.dashboard.auth import restore_session, sign_in
from app.dashboard.page import render_dashboard_page


load_dotenv()


st.set_page_config(
    page_title="Dashboard financiero",
    layout="wide",
)


def render_login() -> None:
    st.title("Dashboard financiero")
    st.caption("Primera version funcional: login, sesion y datos del usuario autenticado.")

    default_email = os.getenv("SUPABASE_EMAIL", "").strip()
    default_password = os.getenv("SUPABASE_PASSWORD", "").strip()

    with st.form("login_form"):
        email = st.text_input("Email", value=default_email)
        password = st.text_input("Password", type="password", value=default_password)
        submitted = st.form_submit_button("Iniciar sesion", use_container_width=True)

    if submitted:
        try:
            sign_in(email, password)
            st.success("Sesion iniciada correctamente.")
            st.rerun()
        except Exception as error:
            st.error(f"No se pudo iniciar sesion: {error}")


def main() -> None:
    try:
        client, auth_user = restore_session()
    except Exception as error:
        st.error(f"Error de configuracion: {error}")
        st.stop()

    if not auth_user:
        render_login()
        st.stop()

    render_dashboard_page(client, auth_user)


if __name__ == "__main__":
    main()
