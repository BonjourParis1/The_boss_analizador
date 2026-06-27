"""
app.py — "Guía Experto de Trading" · terminal profesional en tiempo real.

Ejecutar:
    streamlit run app.py
Recomendado (solo tu PC, más seguro):
    streamlit run app.py --server.address=localhost

Flujo: login triple clave -> selección de activo -> datos reales -> indicadores
+ noticias -> motor de decisiones -> visualización en vivo (auto-refresco) ->
registro de decisiones en Supabase -> historial, radar, backtest y ML.
"""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from analysis import auto_learn
from analysis.backtest import run_backtest
from analysis.engine import BUY, HOLD, SELL, analyze
from analysis.indicators import compute_all
from analysis.news import get_news
from analysis.patterns import read_candles
from brain import llm
from ingest import content as ingest
from config import SYMBOLS, SYMBOLS_BY_KEY, settings
from data.connectors import fetch_with_retry
from data.realtime import fast_quote, is_realtime
from db.store import (BACKEND, get_history, get_stats, init_db,
                      save_recommendation, save_user_decision)
from ml import model as ml_model
from notifications import email_alerts
from ui import components as C
from ui import theme as T
from ui.auth_ui import is_authenticated, logout, render_login

st.set_page_config(page_title="Guía Experto de Trading", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown(T.CSS, unsafe_allow_html=True)


# --------------------------- Cache de datos --------------------------------
@st.cache_data(show_spinner=False, ttl=settings.refresh_seconds)
def load_market(symbol_key: str, interval: str, limit: int):
    df = fetch_with_retry(SYMBOLS_BY_KEY[symbol_key], interval=interval, limit=limit)
    return compute_all(df)


@st.cache_data(show_spinner=False, ttl=300)  # noticias: refresco cada 5 min
def load_news(symbol_key: str):
    return get_news(SYMBOLS_BY_KEY[symbol_key])


# --------------------------------- Login -----------------------------------
try:
    init_db()
except Exception as e:  # noqa: BLE001
    st.sidebar.warning(f"Aviso base de datos ({BACKEND}): {e}")

if not is_authenticated():
    render_login()
    st.stop()


# ------------------------------- Barra lateral ------------------------------
with st.sidebar:
    st.markdown(f"<h2 style='color:{T.BLUE};margin-bottom:0;'>📊 GUÍA EXPERTO</h2>"
                f"<div class='gx-tag'>Terminal de trading · {BACKEND}</div><br>",
                unsafe_allow_html=True)

    st.session_state["symbol_key"] = st.selectbox(
        "Activo", options=[s.key for s in SYMBOLS],
        format_func=lambda k: f"{SYMBOLS_BY_KEY[k].label}  ·  {SYMBOLS_BY_KEY[k].type}",
        index=[s.key for s in SYMBOLS].index(st.session_state.get("symbol_key", SYMBOLS[0].key)),
    )
    st.session_state["interval"] = st.selectbox("Temporalidad", ["1m", "5m", "15m", "1h", "1d"],
                                                index=1)
    st.session_state["limit"] = st.slider("Velas", 60, 500, 200, step=20)
    st.session_state["live"] = st.toggle("🔴 Tiempo real", value=True)
    st.session_state["refresh"] = st.number_input("Refresco cripto (seg)", 1, 120,
                                                   value=settings.refresh_seconds)
    if not settings.alpha_vantage_key:
        st.caption("⚠️ Sin ALPHA_VANTAGE_API_KEY: el forex usa Yahoo Finance "
                   "(menos intradía). Añádela en .env para datos pro.")
    st.divider()
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        logout()
        st.rerun()


tab_live, tab_radar, tab_brain, tab_hist, tab_back, tab_ml = st.tabs(
    ["🖥️ Terminal", "📡 Radar de mercado", "🧠 Cerebro IA",
     "📜 Historial", "⏮ Backtesting", "🤖 Aprendizaje"]
)


# ============================== TAB: TERMINAL (tiempo real) =================
def render_terminal():
    sk = st.session_state["symbol_key"]
    interval = st.session_state["interval"]
    limit = st.session_state["limit"]
    symbol = SYMBOLS_BY_KEY[sk]

    try:
        df = load_market(sk, interval, limit)
    except Exception as e:  # noqa: BLE001
        st.error(f"No se pudieron obtener datos de {symbol.label}: {e}")
        return

    digest = load_news(sk)
    reading = read_candles(df)
    quote = fast_quote(symbol)              # precio en vivo (solo cripto)
    sig = analyze(sk, df, news_score=digest.score, candles=reading)

    # Encabezado tipo ticker (precio en vivo si es cripto)
    st.markdown(C.ticker_header(symbol.label, df, symbol.type, quote=quote,
                                updated=datetime.now().strftime("%H:%M:%S")),
                unsafe_allow_html=True)

    col_chart, col_side = st.columns([3, 1.25], gap="medium")
    with col_chart:
        st.plotly_chart(C.pro_chart(symbol.label, df, sig.support, sig.resistance),
                        use_container_width=True,
                        config={"scrollZoom": True, "displayModeBar": False})
        st.plotly_chart(C.indicator_panel(df), use_container_width=True,
                        config={"displayModeBar": False})

    with col_side:
        st.markdown(C.signal_html(sig, symbol.label), unsafe_allow_html=True)
        st.plotly_chart(C.confidence_gauge(sig), use_container_width=True,
                        config={"displayModeBar": False})
        st.markdown(C.candles_html(reading), unsafe_allow_html=True)

        if sig.is_strong:
            st.toast(f"{sig.icon} Señal FUERTE de {sig.action} en {symbol.label}", icon="🔔")
            st.markdown("<audio autoplay><source "
                        "src='https://actions.google.com/sounds/v1/alarms/beep_short.ogg'"
                        " type='audio/ogg'></audio>", unsafe_allow_html=True)
            if email_alerts.is_enabled():
                email_alerts.send_signal_alert(sig, symbol.label)

        with st.expander("🧠 Lectura del experto", expanded=True):
            for r in sig.reasons:
                st.markdown(f"- {r}")
            for n in sig.beginner_notes:
                st.caption(n)

        # Registro de decisión
        st.markdown("<div class='gx-tag'>Registrar mi operación</div>", unsafe_allow_html=True)
        note = st.text_input("Nota", key="decision_note", label_visibility="collapsed",
                             placeholder="Nota (opcional)")
        b1, b2, b3 = st.columns(3)

        def _record(action: str):
            try:
                rec_id = save_recommendation(sig)
                save_user_decision(rec_id, sk, action, sig.action, sig.price,
                                   st.session_state.get("decision_note", ""))
                st.success(f"Registrado: {action}")
            except Exception as e:  # noqa: BLE001
                st.error(f"No se pudo guardar: {e}")

        if b1.button("📈 Compré", use_container_width=True):
            _record(BUY)
        if b2.button("📉 Vendí", use_container_width=True):
            _record(SELL)
        if b3.button("⏸ Mantuve", use_container_width=True):
            _record(HOLD)

        st.markdown(C.news_html(digest), unsafe_allow_html=True)


with tab_live:
    _symbol = SYMBOLS_BY_KEY[st.session_state["symbol_key"]]
    # Solo cripto tiene streaming real gratuito -> auto-refresco en vivo.
    # Forex/acciones: APIs gratuitas limitadas -> actualización manual.
    if is_realtime(_symbol) and st.session_state.get("live"):
        _run_every = st.session_state["refresh"]
    else:
        _run_every = None
        if not is_realtime(_symbol):
            st.caption("ℹ️ Forex/acciones usan datos con APIs gratuitas limitadas "
                       "(sin tick a tick). Pulsa **Actualizar** para refrescar.")
            if st.button("🔄 Actualizar"):
                load_market.clear()
    _live_fragment = st.fragment(run_every=_run_every)(render_terminal)
    _live_fragment()


# ============================== TAB: RADAR =================================
with tab_radar:
    st.subheader("📡 Radar de mercado — escanea todos los activos")
    st.caption("Calcula la señal del experto para cada activo y los ordena por confianza.")
    if st.button("🔍 Escanear ahora"):
        rows = []
        prog = st.progress(0.0)
        for i, s in enumerate(SYMBOLS):
            try:
                d = load_market(s.key, st.session_state["interval"], 120)
                sg = analyze(s.key, d)
                rows.append({"Activo": s.label, "Tipo": s.type, "Señal": f"{sg.icon} {sg.action}",
                             "Confianza %": sg.confidence, "Precio": sg.price, "RSI": sg.rsi})
            except Exception:
                rows.append({"Activo": s.label, "Tipo": s.type, "Señal": "—",
                             "Confianza %": 0, "Precio": None, "RSI": None})
            prog.progress((i + 1) / len(SYMBOLS))
        import pandas as pd
        df_radar = pd.DataFrame(rows).sort_values("Confianza %", ascending=False)
        st.dataframe(df_radar, use_container_width=True, hide_index=True)


# ============================== TAB: CEREBRO IA ============================
with tab_brain:
    st.subheader("🧠 Cerebro IA — razonamiento con Claude")
    if not llm.is_available():
        st.info("Para activar el razonamiento en lenguaje natural y el análisis de "
                "contenido, añade tu **ANTHROPIC_API_KEY** en el archivo `.env` "
                "(tiene coste por uso). El resto del sistema funciona sin ella.")
    else:
        st.caption(f"Modelo: {settings.anthropic_model}")

    c_reason, c_ingest = st.columns(2, gap="large")

    with c_reason:
        st.markdown("#### 🗣️ Que el experto IA analice el activo actual")
        sk = st.session_state["symbol_key"]
        if st.button("Analizar con IA", disabled=not llm.is_available()):
            with st.spinner("Pensando como un analista senior..."):
                try:
                    df = load_market(sk, st.session_state["interval"],
                                     st.session_state["limit"])
                    reading = read_candles(df)
                    digest = load_news(sk)
                    sig = analyze(sk, df, news_score=digest.score, candles=reading)
                    text = llm.reason_trade(sig, SYMBOLS_BY_KEY[sk].label,
                                            [i.title for i in digest.items])
                    st.markdown(text)
                except Exception as e:  # noqa: BLE001
                    st.error(f"No se pudo generar el análisis: {e}")

    with c_ingest:
        st.markdown("#### 📥 Procesar contenido que le adjuntes")
        kind = st.radio("Tipo", ["Texto", "YouTube (URL)"], horizontal=True,
                        label_visibility="collapsed")
        if kind == "Texto":
            txt = st.text_area("Pega aquí un artículo, notas o estrategia", height=160)
            if st.button("Analizar contenido"):
                with st.spinner("Analizando..."):
                    try:
                        res = ingest.ingest_text(txt)
                        st.caption(f"Sentimiento: {res.sentiment:+.2f}")
                        st.markdown(res.analysis)
                    except Exception as e:  # noqa: BLE001
                        st.error(f"Error: {e}")
        else:
            url = st.text_input("URL de YouTube", placeholder="https://youtu.be/...")
            st.caption("Se analiza la **transcripción** (lo que se dice), no la imagen.")
            if st.button("Analizar video"):
                with st.spinner("Bajando transcripción y analizando..."):
                    try:
                        res = ingest.ingest_youtube(url)
                        st.caption(f"Sentimiento de la transcripción: {res.sentiment:+.2f}")
                        st.markdown(res.analysis)
                    except Exception as e:  # noqa: BLE001
                        st.error(f"No se pudo procesar el video (¿tiene transcripción?): {e}")


# ============================== TAB: HISTORIAL =============================
with tab_hist:
    st.subheader("📜 Historial de decisiones")
    try:
        stats = get_stats()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Recomendaciones", stats["recomendaciones_generadas"])
        m2.metric("Mis decisiones", stats["decisiones_registradas"])
        m3.metric("Coincidencias", stats["coincidencias_con_bot"])
        m4.metric("Tasa coincidencia", f"{stats['tasa_coincidencia_pct']}%")
        hist = get_history(limit=300)
        if hist.empty:
            st.info("Aún no hay decisiones registradas. Ve a la pestaña Terminal.")
        else:
            st.dataframe(hist, use_container_width=True, hide_index=True)
    except Exception as e:  # noqa: BLE001
        st.error(f"No se pudo leer el historial ({BACKEND}): {e}")


# ============================== TAB: BACKTESTING ===========================
with tab_back:
    st.subheader("⏮ Backtesting de la estrategia")
    if st.button("▶ Ejecutar backtest"):
        try:
            df_bt = load_market(st.session_state["symbol_key"],
                                st.session_state["interval"], st.session_state["limit"])
            res = run_backtest(st.session_state["symbol_key"], df_bt)
            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Operaciones", res.trades)
            b2.metric("Aciertos", res.wins)
            b3.metric("Tasa de acierto", f"{res.win_rate}%")
            b4.metric("Retorno", f"{res.total_return_pct}%")
            if not res.equity_curve.empty:
                st.line_chart(res.equity_curve)
            if not res.trade_log.empty:
                st.dataframe(res.trade_log, use_container_width=True, hide_index=True)
        except Exception as e:  # noqa: BLE001
            st.error(f"Error en backtest: {e}")


# ============================== TAB: ML ====================================
with tab_ml:
    st.subheader("🤖 Aprendizaje")
    st.caption("Dos modelos complementarios. Ambos son APOYO probabilístico, no "
               "predicciones garantizadas.")

    st.markdown("### 🧪 Autoaprendizaje del histórico (sin que operes)")
    st.write("Aprende del mercado: etiqueta cada vela por lo que pasó después y "
             "entrena un modelo para anticipar SUBE / LATERAL / BAJA.")
    if st.button("🎓 Entrenar con el histórico de todos los activos"):
        with st.spinner("Descargando históricos y entrenando..."):
            try:
                datasets = []
                for s in SYMBOLS:
                    try:
                        datasets.append(fetch_with_retry(
                            s, interval=st.session_state["interval"], limit=400))
                    except Exception:
                        continue
                rep = auto_learn.train_from_history(datasets)
                st.success(f"Entrenado con {rep.samples} ejemplos. "
                           f"Precisión validada: **{rep.accuracy_cv:.0%}** "
                           f"(horizonte {rep.horizon} velas).")
                st.caption(f"Distribución de clases: {rep.class_counts}")
            except Exception as e:  # noqa: BLE001
                st.error(f"No se pudo entrenar: {e}")

    if auto_learn.model_exists():
        try:
            lbl, proba, hz = auto_learn.predict(load_market(
                st.session_state["symbol_key"], st.session_state["interval"],
                st.session_state["limit"]))
            if lbl:
                st.info(f"Para **{SYMBOLS_BY_KEY[st.session_state['symbol_key']].label}**, "
                        f"el autoaprendizaje anticipa **{lbl}** en las próximas {hz} velas "
                        f"(confianza {proba}%).")
        except Exception as e:  # noqa: BLE001
            st.warning(f"No se pudo predecir: {e}")

    st.divider()
    st.markdown("### 👤 Aprendizaje de tus decisiones")
    st.caption("Aprende qué harías TÚ según los indicadores (requiere decisiones "
               "registradas en la pestaña Terminal).")
    if ml_model.model_exists():
        try:
            pred, p2 = ml_model.predict(load_market(
                st.session_state["symbol_key"], st.session_state["interval"],
                st.session_state["limit"]))
            if pred:
                st.success(f"El modelo cree que elegirías: **{pred}** (confianza {p2}%).")
        except Exception as e:  # noqa: BLE001
            st.warning(f"No se pudo predecir: {e}")
    else:
        st.info("Todavía no hay modelo de tus decisiones. Registra decisiones y entrénalo.")
