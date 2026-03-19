import os

from dotenv import load_dotenv
import streamlit as st

from app.database.supabase_client import get_supabase_client


load_dotenv()


SESSION_STATE_KEY = "supabase_session"
USER_STATE_KEY = "auth_user"


def get_dashboard_client():
    url = os.getenv("SUPABASE_URL", "").strip()
    anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()

    if not url:
        raise RuntimeError("Falta SUPABASE_URL en el archivo .env.")

    if not anon_key:
        raise RuntimeError("Falta SUPABASE_ANON_KEY en el archivo .env.")

    return get_supabase_client(url=url, key=anon_key)


def _save_auth_state(auth_response) -> dict:
    session = auth_response.session
    user = auth_response.user

    if session is None or user is None:
        raise RuntimeError("No se pudo obtener la sesion del usuario.")

    st.session_state[SESSION_STATE_KEY] = {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
    }
    st.session_state[USER_STATE_KEY] = {
        "id": user.id,
        "email": user.email,
        "role": getattr(user, "role", None),
    }
    return st.session_state[USER_STATE_KEY]


def clear_auth_state() -> None:
    st.session_state.pop(SESSION_STATE_KEY, None)
    st.session_state.pop(USER_STATE_KEY, None)


def sign_in(email: str, password: str) -> dict:
    client = get_dashboard_client()
    auth_response = client.auth.sign_in_with_password(
        {
            "email": email.strip(),
            "password": password,
        }
    )
    return _save_auth_state(auth_response)


def get_current_session() -> dict | None:
    return st.session_state.get(SESSION_STATE_KEY)


def restore_session():
    client = get_dashboard_client()
    current_session = get_current_session()

    if not current_session:
        return client, None

    try:
        auth_response = client.auth.set_session(
            current_session["access_token"],
            current_session["refresh_token"],
        )
        user = _save_auth_state(auth_response)
        return client, user
    except Exception:
        clear_auth_state()
        return client, None


def sign_out() -> None:
    client = get_dashboard_client()
    current_session = get_current_session()

    if current_session:
        try:
            client.auth.set_session(
                current_session["access_token"],
                current_session["refresh_token"],
            )
            client.auth.sign_out()
        except Exception:
            pass

    clear_auth_state()
