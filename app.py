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

import autonomous
from analysis import advisor, auto_learn
from analysis.backtest import run_backtest
from analysis.engine import BUY, HOLD, SELL, analyze
from analysis.indicators import compute_all
from analysis.news import get_news
from analysis.patterns import read_candles
from brain import llm
from ingest import content as ingest
from config import GROUPS, SYMBOLS, SYMBOLS_BY_KEY, settings
from data.connectors import fetch_with_retry
from data.realtime import fast_quote, is_realtime
from db.store import (BACKEND, get_history, get_stats, init_db,
                      save_recommendation, save_user_decision)
from ml import model as ml_model
from notifications import email_alerts
import streamlit.components.v1 as components
from ui import components as C
from ui import theme as T
from ui.auth_ui import is_authenticated, logout, render_login
from ui.realtime_chart import stream_chart_html

st.set_page_config(page_title="Guía Experto de Trading", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown(T.CSS, unsafe_allow_html=True)


# --------------------------- Cache de datos --------------------------------
# TTL de 15s: las velas se recargan como mucho cada 15s (protege APIs gratuitas
# como Twelve Data 8/min); el movimiento "en vivo" lo da el tick de la última vela.
@st.cache_data(show_spinner=False, ttl=15)
def load_market(symbol_key: str, interval: str, limit: int):
    df = fetch_with_retry(SYMBOLS_BY_KEY[symbol_key], interval=interval, limit=limit)
    return compute_all(df)


@st.cache_data(show_spinner=False, ttl=300)  # noticias: refresco cada 5 min
def load_news(symbol_key: str):
    return get_news(SYMBOLS_BY_KEY[symbol_key])


@st.cache_data(show_spinner=False, ttl=600)  # backtest: pesado, cache 10 min
def _backtest_cached(symbol_key: str, interval: str, limit: int) -> dict:
    df_bt = load_market(symbol_key, interval, max(limit, 200))
    res = run_backtest(symbol_key, df_bt)
    return {"trades": res.trades, "wins": res.wins, "win_rate": res.win_rate,
            "total_return_pct": res.total_return_pct,
            "equity": res.equity_curve, "trades_df": res.trade_log}


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

    # Filtro por categoría de mercado
    grp = st.selectbox("Mercado", ["Todos"] + GROUPS, index=0)
    opciones = [s.key for s in SYMBOLS if grp == "Todos" or s.group == grp]
    prev = st.session_state.get("symbol_key", SYMBOLS[0].key)
    idx = opciones.index(prev) if prev in opciones else 0
    st.session_state["symbol_key"] = st.selectbox(
        "Activo", options=opciones, index=idx,
        format_func=lambda k: SYMBOLS_BY_KEY[k].label)

    st.session_state["interval"] = st.selectbox(
        "Temporalidad",
        ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1w", "1M"], index=2)
    st.session_state["chart_type"] = st.selectbox(
        "Tipo de gráfico",
        ["🔴 Stream en vivo", "Velas", "Velas 5s", "Velas 30s", "Línea en vivo"], index=0)
    st.session_state["duration"] = st.selectbox(
        "⏱️ Duración de la inversión", ["30s", "1m", "3m", "5m", "15m"], index=1,
        help="El asesor analiza el mercado PARA esta duración y te dice si comprar, "
             "vender o esperar. Si detecta una oportunidad en otra duración, te avisa.")

    with st.expander("⚙️ Indicadores / opciones"):
        st.session_state["show_ma"] = st.checkbox("Medias móviles (SMA/EMA)", value=True)
        st.session_state["show_bb"] = st.checkbox("Bandas de Bollinger", value=True)
        st.session_state["show_vol"] = st.checkbox("Volumen", value=True)
        st.session_state["show_ind"] = st.checkbox("Panel RSI / MACD", value=True)
        st.session_state["limit"] = st.slider("Velas a cargar", 60, 500, 200, step=20)

    st.session_state.setdefault("limit", 200)
    st.session_state["live"] = st.toggle("🔴 Tiempo real", value=True)
    st.session_state["refresh"] = st.number_input("Refresco (seg)", 1, 120,
                                                   value=settings.refresh_seconds)

    st.divider()
    # --- Motor autónomo 24/7 (arranca solo; se puede apagar para descansar) ---
    st.session_state.setdefault("auto_interval", max(60, settings.scan_interval_minutes * 60))
    st.session_state.setdefault("auto_minconf", 65)
    auto_on = st.toggle("🤖 Autónomo 24/7", value=True, key="auto_on",
                        help="Analiza todos los mercados en segundo plano y genera "
                             "operaciones sugeridas. Apágalo para descansar y no gastar recursos.")
    if auto_on and not autonomous.is_running():
        autonomous.start(interval_seconds=st.session_state["auto_interval"],
                         min_confidence=st.session_state["auto_minconf"],
                         timeframe=st.session_state["interval"])
    elif not auto_on and autonomous.is_running():
        autonomous.stop()
    st.caption("🟢 Analizando en segundo plano" if autonomous.is_running()
               else "⚪ Detenido (sin consumo)")

    st.divider()
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        autonomous.stop()
        logout()
        st.rerun()


st.markdown(C.header_bar(autonomous.is_running()), unsafe_allow_html=True)

tab_live, tab_auto, tab_radar, tab_brain, tab_hist, tab_back, tab_ml = st.tabs(
    ["🖥️ Terminal", "🤖 Autónomo", "📡 Radar de mercado", "🧠 Cerebro IA",
     "📜 Historial", "⏮ Backtesting", "🎓 Aprendizaje"]
)


# ============================== TAB: TERMINAL (tiempo real) =================
def _plan_for_duration(sk: str, dur_tuple, news_score):
    """Plan + señal + lectura para una duración, con velas ESTABLES (sin tick).

    Analizar sobre velas cerradas evita que la recomendación cambie cada segundo.
    """
    label, secs, an_interval = dur_tuple
    dfd = load_market(sk, an_interval, 150)
    reading = read_candles(dfd)
    ap = ac = None
    if auto_learn.model_exists():
        try:
            ap, ac, _ = auto_learn.predict(dfd)
        except Exception:
            ap = None
    sg = analyze(sk, dfd, news_score=news_score, candles=reading)
    return advisor.build_plan(sg, ap, ac, force_duration=(label, secs)), sg, reading


def _opportunities(sk: str, chosen: str, news_score):
    """Busca señales fuertes en OTRAS duraciones distintas a la elegida (#7)."""
    out = []
    for dt in advisor.DURATIONS:
        if dt[0] == chosen:
            continue
        try:
            p, _, _ = _plan_for_duration(sk, dt, news_score)
            if p.is_actionable and p.confidence >= 70:
                out.append(p)
        except Exception:
            pass
    return out


def render_side_panel():
    """Panel derecho: PLAN para la duración elegida + oportunidades + registro.

    Se puede auto-refrescar por sí solo sin reiniciar el gráfico de streaming.
    """
    if not is_authenticated():
        return
    sk = st.session_state["symbol_key"]
    symbol = SYMBOLS_BY_KEY[sk]
    duration = st.session_state.get("duration", "1m")
    dtuple = advisor.DURATION_BY_LABEL.get(duration, advisor.DURATION_BY_LABEL["1m"])
    digest = load_news(sk)

    try:
        plan, sig_plan, reading = _plan_for_duration(sk, dtuple, digest.score)
    except Exception as e:  # noqa: BLE001
        st.error(f"Sin datos para {symbol.label}: {e}")
        return
    opportunities = _opportunities(sk, duration, digest.score)

    # Feed: solo cuando cambia la recomendación de la duración elegida
    if plan.is_actionable:
        feed = st.session_state.setdefault("plan_feed", [])
        tag = f"{sk}:{plan.direction}:{plan.duration_label}"
        if not feed or feed[0].get("tag") != tag:
            feed.insert(0, {"tag": tag, "t": datetime.now().strftime("%H:%M:%S"),
                            "txt": f"{plan.icon} {plan.action_label} {symbol.label} · "
                                   f"{plan.duration_label} · {plan.confidence:.0f}%"})
            del feed[30:]
            st.toast(f"{plan.icon} {plan.action_label} {symbol.label} · {duration}", icon="🔔")
            if email_alerts.is_enabled():
                email_alerts.send_signal_alert(sig_plan, symbol.label)

    # Plan de la duración elegida (lo más importante)
    st.markdown(C.trade_plan_html(plan, symbol.label), unsafe_allow_html=True)
    st.caption(f"Análisis para inversión de **{duration}**")
    st.plotly_chart(C.confidence_gauge(sig_plan), use_container_width=True,
                    config={"displayModeBar": False})

    # Oportunidades en OTRAS duraciones (#7)
    if opportunities:
        rows = "".join(
            f"<div class='gx-news'><b>{p.icon} {p.action_label}</b> · vence en "
            f"<b>{p.duration_label}</b> · {p.confidence:.0f}%</div>"
            for p in opportunities[:4])
        st.markdown(f"<div class='gx-card' style='border-color:{T.GOLD};'>"
                    f"<div class='gx-tag'>⚡ Oportunidades en otras duraciones</div>{rows}"
                    f"<div style='font-size:0.72rem;color:#7e8ca3;margin-top:6px;'>"
                    f"Distintas a tu elección ({duration}). Considera si te conviene operar a ese plazo.</div></div>",
                    unsafe_allow_html=True)

    st.markdown(C.candles_html(reading), unsafe_allow_html=True)

    feed = st.session_state.get("plan_feed", [])
    if feed:
        rows = "".join(f"<div class='gx-news'><b>{a['t']}</b> &nbsp; {a['txt']}</div>"
                       for a in feed[:6])
        st.markdown(f"<div class='gx-card'><div class='gx-tag'>🎯 Operaciones sugeridas</div>"
                    f"{rows}</div>", unsafe_allow_html=True)

    with st.expander("🧠 Lectura del experto", expanded=True):
        for r in sig_plan.reasons:
            st.markdown(f"- {r}")

    st.markdown("<div class='gx-tag'>Registrar mi operación</div>", unsafe_allow_html=True)
    st.text_input("Nota", key="decision_note", label_visibility="collapsed",
                  placeholder="Nota (opcional)")
    b1, b2, b3 = st.columns(3)

    def _record(action: str):
        try:
            rec_id = save_recommendation(sig_plan)
            save_user_decision(rec_id, sk, action, sig_plan.action, sig_plan.price,
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


def render_terminal():
    """Modo NO streaming: gráfico Plotly + panel lateral (todo en un fragment)."""
    if not is_authenticated():
        return
    sk = st.session_state["symbol_key"]
    interval = st.session_state["interval"]
    limit = st.session_state["limit"]
    symbol = SYMBOLS_BY_KEY[sk]
    ctype = st.session_state.get("chart_type", "Velas")

    try:
        df = load_market(sk, interval, limit)
    except Exception as e:  # noqa: BLE001
        st.error(f"No se pudieron obtener datos de {symbol.label}: {e}")
        return

    quote = fast_quote(symbol)
    if quote:                                # vela en vivo (visual)
        lp = quote["price"]
        df = df.copy()
        last = df.index[-1]
        df.loc[last, "close"] = lp
        df.loc[last, "high"] = max(df.loc[last, "high"], lp)
        df.loc[last, "low"] = min(df.loc[last, "low"], lp)
        df = compute_all(df.drop(columns=[c for c in df.columns
                                          if c not in ("open", "high", "low", "close", "volume")]))
    reading = read_candles(df)
    sig = analyze(sk, df, candles=reading)

    buf = st.session_state.setdefault(f"ticks_{sk}", [])
    buf.append((datetime.now(), quote["price"] if quote else float(df["close"].iloc[-1])))
    del buf[:-300]

    st.markdown(C.ticker_header(symbol.label, df, symbol.type, quote=quote,
                                updated=datetime.now().strftime("%H:%M:%S")),
                unsafe_allow_html=True)

    col_chart, col_side = st.columns([3.6, 1.3], gap="medium")
    with col_chart:
        cfg = {"scrollZoom": True, "displayModeBar": False}
        if ctype == "Línea en vivo":
            st.plotly_chart(C.live_line_chart(symbol.label, buf), use_container_width=True, config=cfg)
        elif ctype in ("Velas 5s", "Velas 30s"):
            bs = 5 if ctype == "Velas 5s" else 30
            df_sec = C.seconds_ohlc(buf, bs)
            if len(df_sec) < 2:
                st.info(f"⏳ Capturando ticks para velas de {bs}s…")
            st.plotly_chart(C.seconds_candle_chart(symbol.label, df_sec, bs),
                            use_container_width=True, config=cfg)
        else:
            st.plotly_chart(
                C.pro_chart(symbol.label, df, sig.support, sig.resistance,
                            show_ma=st.session_state.get("show_ma", True),
                            show_bb=st.session_state.get("show_bb", True),
                            show_volume=st.session_state.get("show_vol", True)),
                use_container_width=True, config=cfg)
        if st.session_state.get("show_ind", True):
            st.plotly_chart(C.indicator_panel(df), use_container_width=True,
                            config={"displayModeBar": False})
    with col_side:
        render_side_panel()


def _side_refresh(symbol) -> int:
    if symbol.type == "forex":
        return max(15, st.session_state["refresh"])   # protege cuota Twelve Data
    if symbol.type == "stock":
        return max(8, st.session_state["refresh"])
    return max(3, st.session_state["refresh"])         # cripto


with tab_live:
    _symbol = SYMBOLS_BY_KEY[st.session_state["symbol_key"]]
    _ctype = st.session_state.get("chart_type", "Velas")
    _stream = _ctype == "🔴 Stream en vivo" and _symbol.type == "cripto"
    _live = st.session_state.get("live", True)

    if _stream:
        # Gráfico en streaming (se actualiza SOLO en el navegador, tick a tick) +
        # panel lateral que se auto-refresca sin reiniciar el gráfico.
        cL, cR = st.columns([3.6, 1.3], gap="medium")
        with cL:
            components.html(stream_chart_html(_symbol.provider_id,
                                              st.session_state["interval"], 680), height=706)
        with cR:
            st.fragment(run_every=(_side_refresh(_symbol) if _live else None))(render_side_panel)()
    else:
        if _ctype == "🔴 Stream en vivo" and _symbol.type != "cripto":
            st.info("El streaming tick a tick es para criptomonedas. Para este activo se "
                    "muestran velas; cambia el tipo de gráfico o elige una cripto.")
        if not is_realtime(_symbol):
            st.caption("ℹ️ Este activo usa APIs gratuitas limitadas (sin tick a tick).")
            if st.button("🔄 Actualizar"):
                load_market.clear()
            _run_every = None
        elif _live:
            _seconds = _ctype in ("Velas 5s", "Velas 30s", "Línea en vivo")
            if _symbol.type == "cripto":
                _run_every = 1 if _seconds else st.session_state["refresh"]
            elif _symbol.type == "forex":
                _run_every = max(15, st.session_state["refresh"])
            else:
                _run_every = st.session_state["refresh"]
        else:
            _run_every = None
        st.fragment(run_every=_run_every)(render_terminal)()


# ============================== TAB: RADAR =================================
with tab_radar:
    st.subheader("📡 Radar de mercado — automático")
    st.caption("Se alimenta del **motor autónomo** (enciéndelo a la izquierda): escanea "
               "todos los activos solo y los ordena por confianza, sin que pulses nada.")

    @st.fragment(run_every=(4 if autonomous.is_running() else None))
    def _radar_panel():
        if not is_authenticated():
            return
        import pandas as pd
        snap = autonomous.snapshot()
        c1, c2, c3 = st.columns(3)
        c1.metric("Motor", "🟢 Activo" if snap["running"] else "⚪ Detenido")
        c2.metric("Ciclos", snap["cycles"])
        last = snap["last_scan"].strftime("%H:%M:%S") if snap["last_scan"] else "—"
        c3.metric("Último escaneo", last)

        results = snap["results"]
        if results:
            # Mejor oportunidad por activo, ordenadas por confianza
            best = {}
            for r in results:
                if r["symbol"] not in best or r["conf"] > best[r["symbol"]]["conf"]:
                    best[r["symbol"]] = r
            rows = sorted(best.values(), key=lambda r: r["conf"], reverse=True)
            table = [{"Activo": r["symbol"], "Señal": f"{r['icon']} {r['action']}",
                      "Duración": r["dur"], "Confianza %": r["conf"],
                      "Precio": r["price"], "Hora": r["t"]} for r in rows]
            st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
        else:
            st.info("El motor aún no ha encontrado señales fuertes. "
                    "Enciende **🤖 Autónomo 24/7** a la izquierda y espera el primer ciclo."
                    if not snap["running"] else
                    "Analizando todos los mercados… las oportunidades aparecerán aquí.")

    _radar_panel()


# ============================== TAB: AUTÓNOMO ==============================
with tab_auto:
    st.subheader("🤖 Motor autónomo — analiza todos los mercados por ti")
    st.caption("Trabaja en segundo plano aunque no estés mirando. Usa el interruptor "
               "**🤖 Autónomo 24/7** de la izquierda para encenderlo o **apagarlo y "
               "descansar** (al apagarlo deja de consumir recursos).")

    cfg1, cfg2, cfg3 = st.columns([1, 1, 1])
    st.session_state["auto_minconf"] = cfg1.slider(
        "Confianza mínima %", 50, 90, int(st.session_state.get("auto_minconf", 65)))
    mins = cfg2.slider("Escanear cada (min)", 1, 60,
                       max(1, int(st.session_state.get("auto_interval", 300)) // 60))
    st.session_state["auto_interval"] = mins * 60
    if cfg3.button("🔄 Aplicar (reiniciar)", use_container_width=True):
        autonomous.stop()
        autonomous.start(interval_seconds=st.session_state["auto_interval"],
                         min_confidence=st.session_state["auto_minconf"],
                         timeframe=st.session_state["interval"])
        st.success("Motor reiniciado con la nueva configuración.")

    @st.fragment(run_every=(3 if autonomous.is_running() else None))
    def _auto_panel():
        if not is_authenticated():
            return
        snap = autonomous.snapshot()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Estado", "🟢 Activo" if snap["running"] else "⚪ Detenido")
        m2.metric("Ciclos", snap["cycles"])
        m3.metric("Señales totales", snap["found_total"])
        last = snap["last_scan"].strftime("%H:%M:%S") if snap["last_scan"] else "—"
        m4.metric("Último análisis", last)

        st.markdown("#### 🎯 Operaciones sugeridas (todos los mercados)")
        if snap["results"]:
            import pandas as pd
            rows = [{"Hora": r["t"], "Activo": r["symbol"], "Señal": f"{r['icon']} {r['action']}",
                     "Duración": r["dur"], "Confianza %": r["conf"], "Precio": r["price"]}
                    for r in snap["results"]]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Aún sin señales fuertes. El motor sigue analizando…"
                    if snap["running"] else "Motor detenido. Enciéndelo a la izquierda.")

        with st.expander("📋 Registro del motor"):
            for line in snap["log"]:
                st.text(line)

    _auto_panel()


# ============================== TAB: CEREBRO IA ============================
with tab_brain:
    st.subheader("🧠 Cerebro IA — razonamiento con modelo local (open-source)")
    if not llm.is_available():
        st.warning("🧠 El cerebro IA no está disponible en este momento. "
                   "El resto del sistema funciona con normalidad.")
    else:
        st.caption("🧠 Cerebro IA activo")

    # ---- Auto-investigación (noticias + YouTube) ----
    with st.container(border=True):
        st.markdown("#### 🔎 Auto-investigación del mercado")
        ar1, ar2 = st.columns([1, 1])
        auto_inv = ar1.toggle("Investigar cada 5 min", value=False,
                              help="El cerebro consulta noticias (y YouTube si hay clave) "
                                   "del activo actual y las sintetiza solo.")
        if not settings.youtube_api_key:
            ar2.caption("💡 Añade YOUTUBE_API_KEY en .env para incluir videos de YouTube.")

        def _do_research():
            sk = st.session_state["symbol_key"]
            with st.spinner("Investigando noticias y videos…"):
                try:
                    st.markdown(ingest.auto_research(SYMBOLS_BY_KEY[sk]))
                except Exception as e:  # noqa: BLE001
                    st.error(f"No se pudo investigar: {e}")

        if ar2.button("🔎 Investigar ahora"):
            _do_research()
        if auto_inv:
            @st.fragment(run_every=300)
            def _auto_research_frag():
                if is_authenticated():
                    _do_research()
            _auto_research_frag()

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
    st.subheader("⏮ Backtesting — fiabilidad de la estrategia")
    st.caption("**Qué es:** prueba la estrategia del experto sobre el historial del activo "
               "actual para estimar su **tasa de acierto** pasada. Sirve para saber cuánto "
               "fiarte de las señales. Se ejecuta **solo** para el activo elegido.")
    sk = st.session_state["symbol_key"]
    interval = st.session_state["interval"]
    try:
        res = _backtest_cached(sk, interval, st.session_state["limit"])
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Operaciones", res["trades"])
        b2.metric("Aciertos", res["wins"])
        b3.metric("Tasa de acierto", f"{res['win_rate']}%")
        b4.metric("Retorno", f"{res['total_return_pct']}%")
        if res["win_rate"] >= 55:
            st.success(f"En {SYMBOLS_BY_KEY[sk].label} ({interval}), la estrategia acertó "
                       f"el {res['win_rate']}% históricamente. Señales relativamente fiables.")
        elif res["trades"] > 0:
            st.warning(f"Tasa de acierto {res['win_rate']}% en {interval}: fiabilidad media/baja. "
                       "Prioriza la gestión de riesgo y considera otra temporalidad.")
        if res["equity"] is not None and not res["equity"].empty:
            st.line_chart(res["equity"])
        if res["trades_df"] is not None and not res["trades_df"].empty:
            with st.expander("Operaciones simuladas"):
                st.dataframe(res["trades_df"], use_container_width=True, hide_index=True)
    except Exception as e:  # noqa: BLE001
        st.info(f"No hay datos suficientes para el backtest de este activo ahora: {e}")


# ============================== TAB: ML ====================================
with tab_ml:
    st.subheader("🤖 Aprendizaje")
    st.caption("Dos modelos complementarios. Ambos son APOYO probabilístico, no "
               "predicciones garantizadas.")

    st.markdown("### 🧪 Autoaprendizaje del histórico (sin que operes)")
    st.write("Aprende del mercado: etiqueta cada vela por lo que pasó después y "
             "entrena un modelo para anticipar SUBE / LATERAL / BAJA.")

    cc1, cc2, cc3 = st.columns(3)
    horizon = cc1.slider("Horizonte (velas)", 3, 24, 6,
                         help="Cuántas velas hacia adelante se evalúa el resultado.")
    threshold = cc2.slider("Umbral de movimiento %", 0.1, 2.0, 0.4, step=0.1) / 100
    n_assets = cc3.slider("Nº de activos a usar", 3, len(SYMBOLS), min(10, len(SYMBOLS)))

    if st.button("🎓 Entrenar autoaprendizaje"):
        with st.spinner("Descargando históricos y entrenando..."):
            try:
                datasets = []
                for s in SYMBOLS[:n_assets]:
                    try:
                        datasets.append(fetch_with_retry(
                            s, interval=st.session_state["interval"], limit=400))
                    except Exception:
                        continue
                rep = auto_learn.train_from_history(datasets, horizon=horizon, threshold=threshold)
                st.session_state["auto_report"] = rep
                st.success(f"Entrenado con {rep.samples} ejemplos · "
                           f"precisión validada **{rep.accuracy_cv:.0%}** · "
                           f"horizonte {rep.horizon} velas.")
            except Exception as e:  # noqa: BLE001
                st.error(f"No se pudo entrenar: {e}")

    rep = st.session_state.get("auto_report")
    if rep:
        mm1, mm2, mm3 = st.columns(3)
        mm1.metric("Ejemplos", rep.samples)
        mm2.metric("Precisión validada", f"{rep.accuracy_cv:.0%}")
        mm3.metric("Horizonte", f"{rep.horizon} velas")
        import pandas as pd
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Distribución de clases (qué pasó tras cada vela)")
            st.bar_chart(pd.Series(rep.class_counts))
        with c2:
            st.caption("Importancia de cada indicador para el modelo")
            st.bar_chart(pd.Series(rep.importances))
        if rep.accuracy_cv < 0.45:
            st.warning("Precisión baja: este mercado/temporalidad es poco predecible. "
                       "Úsalo solo como apoyo y prioriza la gestión de riesgo.")

    if auto_learn.model_exists():
        try:
            lbl, proba, hz = auto_learn.predict(load_market(
                st.session_state["symbol_key"], st.session_state["interval"],
                st.session_state["limit"]))
            if lbl:
                st.info(f"📍 Para **{SYMBOLS_BY_KEY[st.session_state['symbol_key']].label}**, "
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
