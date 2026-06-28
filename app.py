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
if not st.session_state.get("_db_inited"):   # solo una vez por sesión (login rápido)
    try:
        init_db()
    except Exception as e:  # noqa: BLE001
        st.sidebar.warning(f"Aviso base de datos ({BACKEND}): {e}")
    st.session_state["_db_inited"] = True

if not is_authenticated():
    render_login()
    st.stop()

# Valores por defecto (los controles principales viven en la franja superior)
for _k, _v in {"grp": "Todos", "symbol_key": SYMBOLS[0].key, "interval": "5m",
               "duration": "1m", "chart_type": "🔴 Stream en vivo", "live": True,
               "limit": 200, "refresh": settings.refresh_seconds}.items():
    st.session_state.setdefault(_k, _v)


# ------------------------------- Barra lateral (herramientas) ---------------
with st.sidebar:
    st.markdown(f"<div style='font-family:Space Grotesk;font-weight:700;font-size:1.05rem;"
                f"background:linear-gradient(90deg,{T.BLUE},{T.GREEN});"
                f"-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>"
                f"◢ GUÍA EXPERTO</div>", unsafe_allow_html=True)

    # --- Motor autónomo 24/7 (arranca solo; se puede apagar para descansar) ---
    st.session_state.setdefault("auto_interval", max(60, settings.scan_interval_minutes * 60))
    st.session_state.setdefault("auto_minconf", 65)
    auto_on = st.toggle("🤖 Autónomo 24/7", value=True, key="auto_on",
                        help="Analiza todos los mercados en segundo plano. Apágalo "
                             "para descansar y no gastar recursos.")
    if auto_on and not autonomous.is_running():
        autonomous.start(interval_seconds=st.session_state["auto_interval"],
                         min_confidence=st.session_state["auto_minconf"],
                         timeframe=st.session_state.get("interval", "5m"))
    elif not auto_on and autonomous.is_running():
        autonomous.stop()

    # --- Watchlist: activos del mercado elegido con su señal del motor ---
    _grp = st.session_state.get("grp", "Todos")
    _wl = [s for s in SYMBOLS if _grp == "Todos" or s.group == _grp]
    if _grp == "Todos":
        _wl = _wl[:12]
    _snap = autonomous.snapshot()
    _sig = {}
    for _r in _snap.get("results", []):
        if _r["symbol"] not in _sig or _r["conf"] > _sig[_r["symbol"]]["conf"]:
            _sig[_r["symbol"]] = _r
    st.markdown(f"<div class='gx-tag' style='margin-top:2px;'>⭐ Watchlist · {_grp}</div>",
                unsafe_allow_html=True)
    for _s in _wl:
        _info = _sig.get(_s.label)
        _badge = f"{_info['icon']} {_info['conf']:.0f}%" if _info else "·"
        _sel = "🔹" if _s.key == st.session_state.get("symbol_key") else ""
        if st.button(f"{_sel}{_s.label}　{_badge}", key=f"wl_{_s.key}",
                     use_container_width=True):
            st.session_state["symbol_key"] = _s.key
            st.rerun()

    with st.expander("⚙️ Indicadores y opciones", expanded=False):
        st.session_state["show_ma"] = st.checkbox("Medias móviles (SMA/EMA)", value=True)
        st.session_state["show_bb"] = st.checkbox("Bandas de Bollinger", value=True)
        st.session_state["show_vol"] = st.checkbox("Volumen", value=True)
        st.session_state["show_ind"] = st.checkbox("Panel RSI / MACD", value=True)
        st.session_state["limit"] = st.slider("Velas a cargar", 60, 500, 200, step=20)
        st.session_state["refresh"] = st.number_input("Refresco (seg)", 1, 120,
                                                       value=settings.refresh_seconds)
        st.session_state["auto_minconf"] = st.slider("Confianza mín. autónomo %", 50, 90,
                                                     int(st.session_state["auto_minconf"]))

    st.caption("🟢 Motor activo" if autonomous.is_running() else "⚪ Motor detenido")
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


@st.cache_data(show_spinner=False, ttl=20)  # cacheado: panel más rápido y menos llamadas
def _opportunities(sk: str, chosen: str, news_score):
    """Busca señales fuertes en OTRAS duraciones distintas a la elegida (#7)."""
    out = []
    for dt in advisor.DURATIONS:
        if dt[0] == chosen:
            continue
        try:
            p, _, _ = _plan_for_duration(sk, dt, news_score)
            if p.is_actionable and p.confidence >= 70:
                out.append({"icon": p.icon, "action_label": p.action_label,
                            "duration_label": p.duration_label, "confidence": p.confidence})
        except Exception:
            pass
    return out


INTERVALS = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1w", "1M"]
CHART_TYPES = ["🔴 Stream en vivo", "Velas", "Velas 5s", "Velas 30s", "Línea en vivo"]
DUR_LABELS = ["30s", "1m", "3m", "5m", "15m"]


def render_toolbar():
    """Controles compactos en franja horizontal superior (estilo IQ Option)."""
    c = st.columns([1.1, 1.7, 1.0, 1.2, 1.1, 0.7])
    grupos = ["Todos"] + GROUPS
    grp = c[0].selectbox("Mercado", grupos,
                         index=grupos.index(st.session_state.get("grp", "Todos")),
                         help="Filtra por categoría de activo.")
    st.session_state["grp"] = grp
    opciones = [s.key for s in SYMBOLS if grp == "Todos" or s.group == grp]
    prev = st.session_state.get("symbol_key", SYMBOLS[0].key)
    sidx = opciones.index(prev) if prev in opciones else 0
    st.session_state["symbol_key"] = c[1].selectbox(
        "Activo", opciones, index=sidx, format_func=lambda k: SYMBOLS_BY_KEY[k].label)
    st.session_state["interval"] = c[2].selectbox(
        "Temporalidad", INTERVALS, index=INTERVALS.index(st.session_state.get("interval", "5m")),
        help="Marco temporal de las velas del gráfico.")
    st.session_state["chart_type"] = c[3].selectbox(
        "Gráfico", CHART_TYPES, index=CHART_TYPES.index(st.session_state.get("chart_type", CHART_TYPES[0])),
        help="«Stream en vivo» (cripto) fluctúa tick a tick como IQ Option.")
    st.session_state["duration"] = c[4].selectbox(
        "⏱️ Duración", DUR_LABELS, index=DUR_LABELS.index(st.session_state.get("duration", "1m")),
        help="El asesor analiza varias temporalidades PARA este plazo y MANTIENE la "
             "recomendación durante ese tiempo (no cambia cada minuto).")
    st.session_state["live"] = c[5].toggle("🔴 Live", value=st.session_state.get("live", True))


@st.cache_data(show_spinner=False, ttl=10)
def _consensus_for(sk: str, duration: str, news_score):
    """Plan MULTI-TEMPORALIDAD (consenso ponderado) + señal/lectura base."""
    dtuple = advisor.DURATION_BY_LABEL.get(duration, advisor.DURATION_BY_LABEL["1m"])
    per_tf, sig_main, reading = [], None, None
    for tf, w in advisor.CONFIRM_TFS.get(duration, advisor.CONFIRM_TFS["1m"]):
        try:
            dfd = load_market(sk, tf, 150)
            rd = read_candles(dfd)
            sg = analyze(sk, dfd, news_score=news_score, candles=rd)
            per_tf.append((tf, w, sg))
            if sig_main is None:
                sig_main, reading = sg, rd
        except Exception:
            pass
    if not per_tf:
        raise RuntimeError("sin datos de mercado")
    ap = ac = None
    if auto_learn.model_exists():
        try:
            ap, ac, _ = auto_learn.predict(load_market(sk, dtuple[2], 150))
        except Exception:
            ap = None
    try:
        wr = _backtest_cached(sk, dtuple[2], 200)["win_rate"]
    except Exception:
        wr = None
    plan = advisor.consensus_plan(per_tf, (dtuple[0], dtuple[1]), ap, ac, wr)
    return plan, sig_main, reading


def compute_locked_plan(sk: str, duration: str, news_score):
    """Multi-TF + BLOQUEO: mantiene el plan durante la duración salvo reversión fuerte."""
    import time as _t
    plan, sig_main, reading = _consensus_for(sk, duration, news_score)
    key = f"lock:{sk}:{duration}"
    now = _t.time()
    lock = st.session_state.get(key)
    remaining = 0
    if lock and now < lock["until"]:
        reversal = (plan.is_actionable and plan.direction != lock["dir"]
                    and plan.confidence >= 80)
        if reversal:
            st.session_state[key] = {"dir": plan.direction,
                                     "until": now + max(plan.expiry_seconds, 30), "plan": plan}
            remaining = int(plan.expiry_seconds)
        else:
            plan = lock["plan"]
            remaining = int(lock["until"] - now)
    elif plan.is_actionable:
        st.session_state[key] = {"dir": plan.direction,
                                 "until": now + max(plan.expiry_seconds, 30), "plan": plan}
        remaining = int(plan.expiry_seconds)
    return plan, sig_main, reading, remaining


def render_strip():
    """Franja superior horizontal: PLAN + oportunidades + mejores del mercado."""
    if not is_authenticated():
        return
    sk = st.session_state["symbol_key"]
    symbol = SYMBOLS_BY_KEY[sk]
    duration = st.session_state.get("duration", "1m")
    digest = load_news(sk)
    try:
        plan, sig_main, reading, remaining = compute_locked_plan(sk, duration, digest.score)
    except Exception:
        st.info(f"Cargando datos de {symbol.label}…")
        return
    st.session_state["_cur"] = {"reasons": plan.rationale,
                                "sig_action": sig_main.action, "price": sig_main.price}

    if plan.is_actionable:
        tag = f"{sk}:{plan.direction}:{duration}"
        if st.session_state.get("_last_tag") != tag:
            st.session_state["_last_tag"] = tag
            st.toast(f"{plan.icon} {plan.action_label} {symbol.label} · {duration}", icon="🔔")
            feed = st.session_state.setdefault("plan_feed", [])
            feed.insert(0, {"t": datetime.now().strftime("%H:%M:%S"),
                            "txt": f"{plan.icon} {plan.action_label} {symbol.label} · {duration} · {plan.confidence:.0f}%"})
            del feed[30:]
            if email_alerts.is_enabled():
                email_alerts.send_signal_alert(sig_main, symbol.label)

    opportunities = _opportunities(sk, duration, digest.score)
    snap = autonomous.snapshot()
    market_rows = ""
    if snap.get("results"):
        best = {}
        for r in snap["results"]:
            if r["symbol"] not in best or r["conf"] > best[r["symbol"]]["conf"]:
                best[r["symbol"]] = r
        for r in sorted(best.values(), key=lambda r: r["conf"], reverse=True)[:3]:
            market_rows += (f"<div class='gx-news'>{r['icon']} <b>{r['symbol']}</b> · "
                            f"{r['dur']} · {r['conf']:.0f}%</div>")

    color = T.GREEN if plan.direction == "SUBE" else T.RED if plan.direction == "BAJA" else T.GOLD
    venc = f"vence en {remaining}s" if remaining else "—"
    s = st.columns([1.8, 1.5, 1.4])
    with s[0]:
        st.markdown(
            f"<div class='gx-card' style='border:2px solid {color};margin-bottom:6px;'>"
            f"<div class='gx-tag'>🎯 Plan · {symbol.label} · inversión {duration}</div>"
            f"<div style='display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;'>"
            f"<span style='font-size:1.7rem;font-weight:800;color:{color};'>{plan.icon} {plan.action_label}</span>"
            f"<span style='font-size:1.15rem;font-weight:700;'>{plan.confidence:.0f}%</span>"
            f"<span style='font-size:0.85rem;color:{T.MUTED};'>{venc}</span></div></div>",
            unsafe_allow_html=True)
    with s[1]:
        if opportunities:
            rows = "".join(f"<div class='gx-news'>{p['icon']} {p['action_label']} · "
                           f"{p['duration_label']} · {p['confidence']:.0f}%</div>"
                           for p in opportunities[:3])
        else:
            rows = "<div style='color:#7e8ca3;font-size:0.85rem;'>Sin señales en otras duraciones.</div>"
        st.markdown(f"<div class='gx-card' style='margin-bottom:6px;'>"
                    f"<div class='gx-tag'>⚡ Otras duraciones</div>{rows}</div>", unsafe_allow_html=True)
    with s[2]:
        body = market_rows or "<div style='color:#7e8ca3;font-size:0.85rem;'>Motor analizando…</div>"
        st.markdown(f"<div class='gx-card' style='margin-bottom:6px;'>"
                    f"<div class='gx-tag'>🏆 Mejores del mercado</div>{body}</div>", unsafe_allow_html=True)


def render_chart_full():
    """Gráfico Plotly a pantalla completa (modos no-stream)."""
    if not is_authenticated():
        return
    sk = st.session_state["symbol_key"]
    symbol = SYMBOLS_BY_KEY[sk]
    interval = st.session_state["interval"]
    limit = st.session_state.get("limit", 200)
    ctype = st.session_state.get("chart_type", "Velas")
    try:
        df = load_market(sk, interval, limit)
    except Exception as e:  # noqa: BLE001
        st.error(f"No se pudieron obtener datos de {symbol.label}: {e}")
        return
    quote = fast_quote(symbol)
    if quote:
        lp = quote["price"]
        df = df.copy()
        last = df.index[-1]
        df.loc[last, "close"] = lp
        df.loc[last, "high"] = max(df.loc[last, "high"], lp)
        df.loc[last, "low"] = min(df.loc[last, "low"], lp)
        df = compute_all(df.drop(columns=[c for c in df.columns
                                          if c not in ("open", "high", "low", "close", "volume")]))
    buf = st.session_state.setdefault(f"ticks_{sk}", [])
    buf.append((datetime.now(), quote["price"] if quote else float(df["close"].iloc[-1])))
    del buf[:-300]
    sig = analyze(sk, df, candles=read_candles(df))
    st.markdown(C.ticker_header(symbol.label, df, symbol.type, quote=quote,
                                updated=datetime.now().strftime("%H:%M:%S")), unsafe_allow_html=True)
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


def render_details():
    """Detalle bajo el gráfico: lectura del experto, registro y noticias."""
    if not is_authenticated():
        return
    sk = st.session_state["symbol_key"]
    cur = st.session_state.get("_cur") or {}
    d1, d2, d3 = st.columns([1.3, 1, 1.5])
    with d1:
        with st.expander("🧠 Lectura del experto (multi-temporalidad)", expanded=True):
            for r in (cur.get("reasons") or ["Analizando el mercado…"]):
                st.markdown(f"- {r}")
    with d2:
        st.markdown("<div class='gx-tag'>Registrar mi operación</div>", unsafe_allow_html=True)
        st.text_input("Nota", key="decision_note", label_visibility="collapsed",
                      placeholder="Nota (opcional)")

        def _record(action):
            try:
                from analysis.engine import Signal  # noqa: F401
                price = cur.get("price", 0.0)
                bot = cur.get("sig_action", "MANTENER")
                # Guardamos una recomendación mínima basada en el contexto actual
                rid = None
                from db.store import save_recommendation as _sr, save_user_decision as _sd
                # Reconstruimos una señal ligera para el registro
                import analysis.engine as _eng
                sig = _eng.Signal(sk, bot, 0.0, price)
                rid = _sr(sig)
                _sd(rid, sk, action, bot, price, st.session_state.get("decision_note", ""))
                st.success(f"Registrado: {action}")
            except Exception as e:  # noqa: BLE001
                st.error(f"No se pudo guardar: {e}")

        bb = st.columns(3)
        if bb[0].button("📈", use_container_width=True, help="Registrar COMPRA"):
            _record(BUY)
        if bb[1].button("📉", use_container_width=True, help="Registrar VENTA"):
            _record(SELL)
        if bb[2].button("⏸", use_container_width=True, help="Registrar MANTENER"):
            _record(HOLD)
    with d3:
        try:
            st.markdown(C.news_html(load_news(sk)), unsafe_allow_html=True)
        except Exception:
            pass


def _side_refresh(symbol) -> int:
    if symbol.type == "forex":
        return max(15, st.session_state.get("refresh", 5))   # protege cuota Twelve Data
    if symbol.type == "stock":
        return max(8, st.session_state.get("refresh", 5))
    return max(3, st.session_state.get("refresh", 5))         # cripto


with tab_live:
    render_toolbar()
    _symbol = SYMBOLS_BY_KEY[st.session_state["symbol_key"]]
    _ctype = st.session_state.get("chart_type", CHART_TYPES[0])
    _live = st.session_state.get("live", True)
    _stream = _ctype == "🔴 Stream en vivo" and _symbol.type == "cripto"
    _strip_refresh = _side_refresh(_symbol) if _live else None

    # Franja superior de avisos (auto-refresca sin reiniciar el gráfico)
    st.fragment(run_every=_strip_refresh)(render_strip)()

    # Gráfico a pantalla completa
    if _stream:
        components.html(stream_chart_html(_symbol.provider_id,
                                          st.session_state["interval"], 520), height=545)
    else:
        if _ctype == "🔴 Stream en vivo" and _symbol.type != "cripto":
            st.caption("ℹ️ El stream tick a tick es solo para cripto; aquí se muestran velas.")
        if not is_realtime(_symbol):
            if st.button("🔄 Actualizar"):
                load_market.clear()
            _chart_refresh = None
        elif _live:
            _seconds = _ctype in ("Velas 5s", "Velas 30s", "Línea en vivo")
            if _symbol.type == "cripto":
                _chart_refresh = 1 if _seconds else st.session_state.get("refresh", 5)
            elif _symbol.type == "forex":
                _chart_refresh = max(15, st.session_state.get("refresh", 5))
            else:
                _chart_refresh = st.session_state.get("refresh", 5)
        else:
            _chart_refresh = None
        st.fragment(run_every=_chart_refresh)(render_chart_full)()

    # Detalle inferior (auto-refresca)
    st.fragment(run_every=_strip_refresh)(render_details)()



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

        research = snap.get("research", [])
        if research:
            st.markdown("#### 🔎 Contexto investigado de las señales (noticias + IA)")
            for r in sorted(research, key=lambda x: x["t"], reverse=True)[:6]:
                with st.expander(f"{r['icon']} {r['label']} · {r['action']} · {r['t']}"):
                    st.markdown(r["text"])

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
        auto_inv = ar1.toggle("Investigar cada 10 min", value=False,
                              help="El cerebro consulta noticias (y YouTube si hay clave) "
                                   "del activo actual y las sintetiza solo.")
        if not settings.youtube_api_key:
            ar2.caption("💡 Añade YOUTUBE_API_KEY en .env para incluir videos de YouTube.")

        def _do_research():
            sk = st.session_state["symbol_key"]
            with st.spinner("Investigando noticias y videos…"):
                try:
                    st.markdown(ingest.auto_research(SYMBOLS_BY_KEY[sk]))
                except Exception:  # noqa: BLE001 — sin exponer detalles/claves
                    st.warning("No se pudo completar la investigación ahora "
                               "(posible límite de la IA). Inténtalo más tarde.")

        if ar2.button("🔎 Investigar ahora"):
            _do_research()
        if auto_inv:
            @st.fragment(run_every=600)
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
