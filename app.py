"""
app.py — Dashboard Streamlit "Guía Experto de Trading".

Ejecutar con:
    streamlit run app.py

Flujo:
  1) Login de administrador con triple clave (ui/auth_ui.py).
  2) Selección de mercado e intervalo.
  3) Descarga de datos reales -> indicadores -> motor de decisiones.
  4) Visualización en tiempo real (auto-refresh configurable).
  5) Registro de tus decisiones en la base de datos.
  6) Historial, estadísticas, backtesting y aprendizaje ML.
"""
from __future__ import annotations

import json
import time

import numpy as np
import streamlit as st

from analysis.backtest import run_backtest
from analysis.engine import BUY, HOLD, SELL, analyze
from analysis.indicators import compute_all
from config import SYMBOLS, SYMBOLS_BY_KEY, settings
from data.connectors import fetch_with_retry
from data.normalizer import latest_tick
from db.database import (get_history, get_stats, init_db, save_recommendation,
                         save_user_decision)
from ml import model as ml_model
from ui import components
from ui.auth_ui import is_authenticated, logout, render_login

st.set_page_config(page_title="Guía Experto de Trading", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")

# Estilo propio (no genérico)
st.markdown("""
<style>
  .stApp { background: #0b0e14; }
  section[data-testid="stSidebar"] { background: #11151f; }
  h1, h2, h3 { color: #e6edf3; }
  div[data-testid="stMetricValue"] { color: #16c784; }
</style>
""", unsafe_allow_html=True)


# ----------------------- Cache de datos (TTL = refresco) -------------------
@st.cache_data(show_spinner=False, ttl=settings.refresh_seconds)
def load_market(symbol_key: str, interval: str, limit: int):
    symbol = SYMBOLS_BY_KEY[symbol_key]
    df = fetch_with_retry(symbol, interval=interval, limit=limit)
    return compute_all(df)


# --------------------------------- Login -----------------------------------
init_db()
if not is_authenticated():
    render_login()
    st.stop()


# ------------------------------- Barra lateral ------------------------------
with st.sidebar:
    st.markdown("## 📊 Guía Experto")
    st.caption("Analista personal de trading en tiempo real")

    symbol_key = st.selectbox(
        "Mercado", options=[s.key for s in SYMBOLS],
        format_func=lambda k: SYMBOLS_BY_KEY[k].label,
    )
    interval = st.selectbox("Intervalo", ["1m", "5m", "15m", "1h", "1d"], index=1)
    limit = st.slider("Velas a cargar", 60, 500, 200, step=20)
    beginner = st.toggle("🔰 Modo principiante", value=True)
    auto = st.toggle("🔄 Auto-refresco", value=True)
    refresh_s = st.number_input("Refresco (segundos)", 3, 120,
                                value=settings.refresh_seconds)

    st.divider()
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        logout()
        st.rerun()

symbol = SYMBOLS_BY_KEY[symbol_key]
tab_live, tab_hist, tab_back, tab_ml = st.tabs(
    ["📈 En vivo", "📜 Historial", "⏮ Backtesting", "🤖 Aprendizaje (ML)"]
)


# ============================== TAB: EN VIVO ===============================
with tab_live:
    try:
        df = load_market(symbol_key, interval, limit)
    except Exception as e:  # noqa: BLE001
        st.error(f"No se pudieron obtener datos de {symbol.label}: {e}")
        st.stop()

    sig = analyze(symbol_key, df)
    tick = latest_tick(symbol_key, df)

    col_main, col_side = st.columns([3, 1.4])

    with col_main:
        st.plotly_chart(components.price_chart(symbol.label, df),
                        use_container_width=True)
        st.plotly_chart(components.indicator_panel(df), use_container_width=True)

    with col_side:
        st.markdown(components.recommendation_html(sig, symbol.label),
                    unsafe_allow_html=True)

        # Alerta visual + sonora para señales fuertes
        if sig.is_strong:
            st.toast(f"{sig.icon} Señal FUERTE de {sig.action} en {symbol.label}!",
                     icon="🔔")
            st.markdown(
                "<audio autoplay><source "
                "src='https://actions.google.com/sounds/v1/alarms/beep_short.ogg'"
                " type='audio/ogg'></audio>", unsafe_allow_html=True)

        st.markdown("#### 🧠 Razones técnicas")
        for r in sig.reasons:
            st.markdown(f"- {r}")

        if beginner:
            st.markdown("#### 🔰 Explicación sencilla")
            for n in sig.beginner_notes:
                st.info(n)

        # --- Registrar mi decisión ---
        st.markdown("#### ✍️ Registrar mi decisión")
        note = st.text_input("Nota (opcional)", key="decision_note")
        c1, c2, c3 = st.columns(3)

        def _record(user_action: str):
            rec_id = save_recommendation(sig)
            save_user_decision(rec_id, symbol_key, user_action,
                               sig.action, sig.price, st.session_state.get("decision_note", ""))
            st.success(f"Registrado: {user_action} en {symbol.label}.")

        if c1.button("📈 Compré", use_container_width=True):
            _record(BUY)
        if c2.button("📉 Vendí", use_container_width=True):
            _record(SELL)
        if c3.button("⏸ Mantuve", use_container_width=True):
            _record(HOLD)

    st.caption(f"Último dato: {tick['timestamp']} · precio {tick['price']} · "
               f"volumen {tick['volume']:.2f}")


# ============================== TAB: HISTORIAL =============================
with tab_hist:
    st.subheader("📜 Historial de decisiones")
    stats = get_stats()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Recomendaciones", stats["recomendaciones_generadas"])
    m2.metric("Mis decisiones", stats["decisiones_registradas"])
    m3.metric("Coincidencias con bot", stats["coincidencias_con_bot"])
    m4.metric("Tasa de coincidencia", f"{stats['tasa_coincidencia_pct']}%")

    hist = get_history(limit=300)
    if hist.empty:
        st.info("Aún no hay decisiones registradas. Ve a la pestaña 'En vivo'.")
    else:
        st.dataframe(hist, use_container_width=True, hide_index=True)


# ============================== TAB: BACKTESTING ===========================
with tab_back:
    st.subheader("⏮ Backtesting de la estrategia")
    st.caption("Aplica las mismas reglas del motor sobre los datos históricos cargados.")
    if st.button("▶ Ejecutar backtest", use_container_width=False):
        try:
            df_bt = load_market(symbol_key, interval, limit)
            res = run_backtest(symbol_key, df_bt)
            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Operaciones", res.trades)
            b2.metric("Aciertos", res.wins)
            b3.metric("Tasa de acierto", f"{res.win_rate}%")
            b4.metric("Retorno total", f"{res.total_return_pct}%")
            if not res.equity_curve.empty:
                st.line_chart(res.equity_curve)
            if not res.trade_log.empty:
                st.dataframe(res.trade_log, use_container_width=True, hide_index=True)
        except Exception as e:  # noqa: BLE001
            st.error(f"Error en backtest: {e}")


# ============================== TAB: ML ====================================
with tab_ml:
    st.subheader("🤖 Aprendizaje a partir de tus decisiones")
    st.caption("Entrena un modelo que aprende qué harías TÚ según los indicadores. "
               "Necesita al menos 10 decisiones registradas para entrenar.")

    pred, proba = ml_model.predict(load_market(symbol_key, interval, limit)) \
        if ml_model.model_exists() else (None, None)
    if pred:
        st.success(f"El modelo cree que tú elegirías: **{pred}** "
                   f"(confianza {proba}%) para {symbol.label}.")
    else:
        st.info("Todavía no hay un modelo entrenado.")

    if st.button("🎓 Entrenar con mi historial"):
        st.warning(
            "El entrenamiento usa los indicadores guardados con cada decisión. "
            "En este prototipo se recomienda acumular decisiones reales antes de "
            "entrenar. (Hook listo en ml/model.py para conectar tu dataset.)")
