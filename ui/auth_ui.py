"""
ui/auth_ui.py — Pantalla de inicio de sesión de administrador con TRIPLE clave.

Renderiza un formulario con tres campos de contraseña. Solo concede acceso si
las tres son correctas. Aplica bloqueo temporal tras varios intentos fallidos.
"""
from __future__ import annotations

import streamlit as st

from config import settings
from security.auth import LoginGuard, admin_keys_exist, verify_triple


def _ensure_state() -> None:
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("login_guard", LoginGuard())


def is_authenticated() -> bool:
    _ensure_state()
    return bool(st.session_state["authenticated"])


def logout() -> None:
    st.session_state["authenticated"] = False


def render_login() -> bool:
    """Dibuja el login. Devuelve True si el usuario queda autenticado."""
    _ensure_state()
    guard: LoginGuard = st.session_state["login_guard"]

    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown(
            "<div style='text-align:center;margin-top:6vh;'>"
            "<div class='logo' style='font-size:2rem;font-weight:700;"
            "font-family:Space Grotesk;background:linear-gradient(90deg,#36c2ff,#21d07a);"
            "-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>"
            "◢ GUÍA EXPERTO</div>"
            "<div style='color:#7e8ca3;margin:4px 0 18px;'>Terminal de trading · "
            "acceso de administrador (triple clave)</div></div>",
            unsafe_allow_html=True)

        if not admin_keys_exist():
            st.error("⚠️ No hay claves configuradas todavía. Ejecuta en la terminal "
                     "**python setup_admin.py** para crear tus tres claves de acceso.")
            return False

        if guard.is_locked:
            st.error(f"🚫 Demasiados intentos fallidos. Espera {guard.seconds_left()} s.")
            return False

        with st.form("login_form", clear_on_submit=False):
            st.text_input("Clave 1", type="password", key="k1", placeholder="Primera clave")
            st.text_input("Clave 2", type="password", key="k2", placeholder="Segunda clave")
            st.text_input("Clave 3", type="password", key="k3", placeholder="Tercera clave")
            submitted = st.form_submit_button("Ingresar →", use_container_width=True,
                                              type="primary")

        if submitted:
            result = verify_triple(st.session_state.get("k1", ""),
                                   st.session_state.get("k2", ""),
                                   st.session_state.get("k3", ""))
            if result.ok:
                guard.register_success()
                st.session_state["authenticated"] = True
                for k in ("k1", "k2", "k3"):
                    st.session_state.pop(k, None)
                st.rerun()
            else:
                guard.register_failure()
                restantes = max(0, settings.auth_max_attempts - guard.failed)
                st.error(f"❌ {result.message} Intentos restantes: {restantes}.")

    return is_authenticated()
