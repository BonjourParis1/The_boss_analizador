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
from pathlib import Path

import streamlit as st

import autonomous
from analysis import advisor, auto_learn, levels as levels_mod, risk, tracker
from analysis.backtest import run_backtest
from analysis.engine import BUY, HOLD, SELL, analyze
from analysis.indicators import compute_all, snapshot_text
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

# Logo de marca (THE BOSS ANALIZADOR): favicon + marca de agua. Usa versiones
# OPTIMIZADAS (favicon.png / logo_wm.png) y cae al original si no están. Si no hay
# imagen, usa un emoji y no muestra marca de agua (sin romper nada).
_ASSETS = Path(__file__).parent / "assets"
_WATERMARK = _ASSETS / "logo_wm.png"
_LOGO = _ASSETS / "logo.png"
_wm_path = _WATERMARK if _WATERMARK.exists() else (_LOGO if _LOGO.exists() else None)

# Favicon como EMOJI (no como imagen PIL): pasar una imagen crea un "media file"
# ligado a la sesión que, tras reiniciar el servidor en la nube, el navegador no
# encuentra y provoca "Bad message format / SessionInfo before initialized". El toro
# se mantiene como marca de agua de fondo.
st.set_page_config(page_title="THE BOSS ANALIZADOR", page_icon="🐂",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown(T.CSS, unsafe_allow_html=True)


def _inject_watermark() -> None:
    """Marca de agua a pantalla completa, DETRÁS del contenido. Se pinta como
    imagen de fondo (no como capa encima), así NO bloquea el scroll ni el layout.
    La opacidad va horneada en el PNG (alpha tenue)."""
    if not _wm_path:
        return
    import base64
    try:
        b64 = base64.b64encode(_wm_path.read_bytes()).decode()
    except Exception:
        return
    st.markdown(
        "<style>"
        "[data-testid='stAppViewContainer']{"
        f"background-image:url('data:image/png;base64,{b64}');"
        "background-repeat:no-repeat;background-position:center 44%;"
        "background-size:min(82vw,1100px);background-attachment:fixed;}"
        "</style>", unsafe_allow_html=True)


_inject_watermark()


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


@st.cache_data(show_spinner=False, ttl=30)   # niveles automáticos del gráfico
def _levels_cached(symbol_key: str, interval: str, limit: int) -> list:
    intr = load_market(symbol_key, interval, limit)
    try:
        daily = load_market(symbol_key, "1d", 90)
    except Exception:
        daily = None
    return levels_mod.compute_levels(intr, daily)


@st.cache_data(show_spinner=False, ttl=3600)  # earnings: consultar 1 vez/hora
def _earnings_cached(symbol_key: str):
    from data.calendar import earnings_soon
    return earnings_soon(SYMBOLS_BY_KEY[symbol_key])


@st.cache_data(show_spinner=False, ttl=300)   # sentimiento social/de mercado
def _social_cached(symbol_key: str):
    from analysis import social
    s = social.market_sentiment(SYMBOLS_BY_KEY[symbol_key])
    return ({"score": s.score, "label": s.label, "source": s.source,
             "emoji": s.emoji, "detail": s.detail} if s else None)


@st.cache_data(show_spinner=False, ttl=900)   # calendario económico macro
def _macro_cached():
    from data.calendar import economic_events, major_event_soon
    return {"events": economic_events(), "major": major_event_soon()}


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

    st.divider()
    # --- Potenciales para invertir: lo que el motor detecta, por confianza ---
    st.markdown("<div class='gx-tag'>🎯 Potenciales para invertir</div>",
                unsafe_allow_html=True)
    _label2key = {s.label: s.key for s in SYMBOLS}
    _snap = autonomous.snapshot()
    _best = {}
    for _r in _snap.get("results", []):
        if _r["symbol"] not in _best or _r["conf"] > _best[_r["symbol"]]["conf"]:
            _best[_r["symbol"]] = _r
    _potentials = sorted(_best.values(), key=lambda r: r["conf"], reverse=True)[:8]
    if _potentials:
        for _r in _potentials:
            _k = _label2key.get(_r["symbol"])
            _sel = "▸ " if _k == st.session_state.get("symbol_key") else ""
            if st.button(f"{_sel}{_r['icon']} {_r['symbol']} · {_r['conf']:.0f}% · {_r['dur']}",
                         key=f"wl_{_k}", use_container_width=True):
                st.session_state["symbol_key"] = _k
                st.rerun()
    else:
        # Aún sin potenciales: lista clicable de activos del mercado elegido
        st.caption("Analizando… mientras tanto, tus mercados:" if autonomous.is_running()
                   else "Enciende «Autónomo 24/7» para rankear potenciales. Tus mercados:")
        _grp = st.session_state.get("grp", "Todos")
        _wl = [s for s in SYMBOLS if _grp == "Todos" or s.group == _grp]
        _wl = _wl[:10]
        for _s in _wl:
            _sel = "▸ " if _s.key == st.session_state.get("symbol_key") else ""
            if st.button(f"{_sel}{_s.label}", key=f"wl_{_s.key}", use_container_width=True):
                st.session_state["symbol_key"] = _s.key
                st.rerun()

    st.divider()
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
        _ff = st.checkbox("🎯 Foco Forex (prioriza tus pares)", value=True,
                          help="El motor escanea TODO el Forex en cada pasada y rota el "
                               "resto de mercados, para no agotar las APIs gratuitas.")
        autonomous.set_forex_focus(_ff)

    with st.expander("💰 Capital y riesgo", expanded=False):
        from db import cloud as _cloud
        # Carga inicial (una vez) desde Supabase/local
        if "capital" not in st.session_state:
            st.session_state["capital"] = float(_cloud.setting_get("capital", 0) or 0)
            st.session_state["risk_pct"] = float(_cloud.setting_get("risk_pct", 3) or 3)
            st.session_state["payout_pct"] = float(_cloud.setting_get("payout_pct", 85) or 85)

        def _save_risk_cfg():
            try:
                _cloud.setting_set("capital", float(st.session_state["capital"]))
                _cloud.setting_set("risk_pct", float(st.session_state["risk_pct"]))
                _cloud.setting_set("payout_pct", float(st.session_state["payout_pct"]))
            except Exception:
                pass

        st.number_input("Capital disponible (USD)", min_value=0.0, step=10.0,
                        key="capital", on_change=_save_risk_cfg,
                        help="Tu base financiera. El sistema calcula cuánto invertir por señal.")
        st.slider("Riesgo máx. por operación %", 1, 15, key="risk_pct",
                  on_change=_save_risk_cfg,
                  help="Tope del % del capital a arriesgar en una sola operación.")
        st.slider("Pago de la opción % (IQ Option)", 60, 95, key="payout_pct",
                  on_change=_save_risk_cfg,
                  help="Rentabilidad que paga tu bróker si aciertas (típico 80–90%).")
        if st.session_state["capital"] > 0:
            st.caption(f"Base: ${st.session_state['capital']:,.0f} · riesgo ≤ "
                       f"{st.session_state['risk_pct']:.0f}% · pago {st.session_state['payout_pct']:.0f}%")

    with st.expander("🔐 Accesos recientes", expanded=False):
        try:
            from db import cloud as _cloud
            _ev = _cloud.access_log_recent(10) if hasattr(_cloud, "access_log_recent") else []
            if not _ev:
                st.caption("Sin registros todavía.")
            else:
                _IC = {"ok": "✅ Entrada", "fallo": "❌ Intento fallido", "logout": "🚪 Salida"}
                for e in _ev:
                    _t = ""
                    if e.get("ts"):
                        _t = datetime.fromtimestamp(e["ts"]).strftime("%d/%m %H:%M:%S")
                    st.caption(f"{_IC.get(e.get('event'), e.get('event',''))} · {_t}")
        except Exception:
            st.caption("Registro de accesos no disponible ahora.")

    st.caption("🟢 Motor activo" if autonomous.is_running() else "⚪ Motor detenido")
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        autonomous.stop()
        logout()
        st.rerun()


st.markdown(C.header_bar(autonomous.is_running()), unsafe_allow_html=True)

tab_live, tab_auto, tab_radar, tab_prec, tab_brain, tab_hist, tab_back, tab_ml = st.tabs(
    ["🖥️ Terminal", "🤖 Autónomo", "📡 Radar", "🎯 Precisión", "🧠 Cerebro IA",
     "📜 Historial", "⏮ Backtest", "🎓 Aprendizaje"]
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
    c = st.columns([1.0, 1.5, 0.95, 1.15, 1.0, 0.85])
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
        bt = _backtest_cached(sk, dtuple[2], 200)
        wr = bt["win_rate"] if bt["trades"] > 0 else None
    except Exception:
        wr = None
    # Aprende de resultados REALES: mezcla la precisión en vivo con el backtest
    lw = tracker.live_winrate(sk)
    if lw is not None:
        wr = round((wr + lw) / 2, 1) if wr is not None else lw
    plan = advisor.consensus_plan(per_tf, (dtuple[0], dtuple[1]), ap, ac, wr)
    # Ajuste por lo APRENDIDO de resultados reales (probabilidad de acierto del modelo)
    try:
        from analysis import self_learn
        from ml.model import extract_features
        feat = extract_features(load_market(sk, dtuple[2], 150))[0].tolist()
        wp = self_learn.win_probability(feat)
        if wp is not None and plan.is_actionable:
            plan.confidence = round(0.7 * plan.confidence + 0.3 * wp, 1)
            plan.rationale = list(plan.rationale) + [
                f"Autoaprendizaje (resultados reales): probabilidad de acierto {wp:.0f}%"]
    except Exception:
        pass
    return plan, sig_main, reading


@st.cache_data(show_spinner=False, ttl=180)  # veredicto IA: máx 1 cálculo/3min por activo
def _ia_verdict_cached(sk: str, duration: str):
    """Veredicto estructurado del cerebro (Gemini/DeepSeek) con TODO el contexto."""
    if not llm.is_available():
        return None
    try:
        digest = load_news(sk)
        _, sig_main, _ = _consensus_for(sk, duration, digest.score)
        ex = []
        so = _social_cached(sk)
        if so:
            ex.append(f"Sentimiento social: {so['label']} ({so['detail']}).")
        try:
            mc = _macro_cached().get("events", [])[:3]
            if mc:
                ex.append("Eventos macro: " + "; ".join(e["event"] for e in mc))
        except Exception:
            pass
        return llm.structured_verdict(sig_main, SYMBOLS_BY_KEY[sk].label,
                                      [i.title for i in digest.items], "  ".join(ex))
    except Exception:
        return None


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
    social = _social_cached(sk)
    # Sentimiento combinado (noticias + social) que SÍ influye en el plan
    combined = digest.score
    if social:
        combined = round((digest.score + social["score"]) / 2, 3)
    try:
        plan, sig_main, reading, remaining = compute_locked_plan(sk, duration, combined)
    except Exception:
        st.info(f"Cargando datos de {symbol.label}…")
        return
    st.session_state["_cur"] = {"reasons": plan.rationale,
                                "sig_action": sig_main.action, "price": sig_main.price}

    # Aprendizaje por resultados: registra la señal (con foto de indicadores) y
    # evalúa las vencidas con el precio real
    try:
        if plan.is_actionable:
            _feat = None
            try:
                from ml.model import extract_features
                _dff = load_market(sk, st.session_state["interval"],
                                   st.session_state.get("limit", 200))
                _feat = extract_features(_dff)[0].tolist()
            except Exception:
                _feat = None
            tracker.record(sk, plan.direction, plan.expiry_seconds, sig_main.price,
                           "terminal", features=_feat)
        tracker.evaluate(sk, sig_main.price)
    except Exception:
        pass

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

    opportunities = _opportunities(sk, duration, combined)
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

    # Guardias de eventos (alta volatilidad): earnings del activo y macro global
    try:
        _earn = _earnings_cached(sk)
    except Exception:
        _earn = None
    try:
        _macro = _macro_cached()
    except Exception:
        _macro = {"events": [], "major": None}
    _warn = []
    if _earn:
        _warn.append(f"Reporte de resultados de {symbol.label} el <b>{_earn}</b>")
    if _macro.get("major"):
        mj = _macro["major"]
        _warn.append(f"Evento macro <b>{mj['event']}</b> ({mj['country']}) {mj['date']}")
    if _warn:
        st.markdown(f"<div class='gx-card' style='border-color:{T.GOLD};margin-bottom:6px;'>"
                    f"<div class='gx-tag' style='color:{T.GOLD};'>⚠️ Evento de alto impacto</div>"
                    + "".join(f"<div>{w}</div>" for w in _warn) +
                    f"<div style='font-size:0.78rem;color:{T.MUTED};margin-top:4px;'>"
                    f"Alta volatilidad: opera con cautela o espera a que pase.</div></div>",
                    unsafe_allow_html=True)

    color = T.GREEN if plan.direction == "SUBE" else T.RED if plan.direction == "BAJA" else T.GOLD
    venc = f"vence en {remaining}s" if remaining else "—"
    _sent = (f"<div style='font-size:0.8rem;color:{T.MUTED};margin-top:4px;'>"
             f"Sentimiento mercado: {social['emoji']} {social['label']} "
             f"<span style='opacity:.7;'>({social['detail']})</span></div>") if social else ""
    # Precisión aprendida (global y del activo) a partir de resultados reales
    _g = tracker.stats()
    _ps = tracker.stats(sk)
    _acc = (f"<div style='font-size:0.8rem;color:{T.MUTED};margin-top:4px;'>"
            f"🎯 Precisión sistema: <b>{_g['accuracy']:.0f}%</b> ({_g['n']}) · "
            f"{symbol.label}: <b>{_ps['accuracy']:.0f}%</b> ({_ps['n']})</div>") if _g['n'] else ""

    # --- Gestor de riesgo: cuánto invertir según tu capital y la ventaja ---
    _risk_html = ""
    _cap = float(st.session_state.get("capital", 0) or 0)
    if plan.is_actionable and _cap > 0:
        _wr = tracker.live_winrate(sk)   # precisión real del activo (si hay muestra)
        _rk = risk.suggest_stake(_cap, plan.confidence, win_rate=_wr,
                                 payout=float(st.session_state.get("payout_pct", 85)) / 100.0,
                                 risk_cap=float(st.session_state.get("risk_pct", 3)) / 100.0)
        if _rk["trade"]:
            _risk_html = (f"<div style='margin-top:6px;border-top:1px solid {T.BORDER};"
                          f"padding-top:6px;font-size:0.9rem;'>💰 <b>Invertir "
                          f"${_rk['stake']:,.2f}</b> ({_rk['pct']:.1f}% del capital) "
                          f"<span style='color:{T.MUTED};font-size:0.78rem;'>· prob {_rk['p']:.0f}% "
                          f"· ventaja {_rk['edge']:+.0f}%</span></div>")
        else:
            _risk_html = (f"<div style='margin-top:6px;border-top:1px solid {T.BORDER};"
                          f"padding-top:6px;font-size:0.84rem;color:{T.GOLD};'>💰 {_rk['advice']}</div>")

    # --- Fusión con el cerebro IA (confirma / discrepa) ---
    ia = _ia_verdict_cached(sk, duration)
    ia_html = ""
    if ia:
        _map = {"COMPRA": "SUBE", "VENTA": "BAJA", "ESPERAR": "ESPERAR"}
        ia_dir = _map.get(str(ia.get("direccion", "")).upper(), "ESPERAR")
        if plan.direction in ("SUBE", "BAJA") and ia_dir == plan.direction:
            badge = f"<span style='color:{T.GREEN};font-weight:700;'>✓ IA confirma</span>"
        elif plan.direction in ("SUBE", "BAJA") and ia_dir in ("SUBE", "BAJA"):
            badge = f"<span style='color:{T.RED};font-weight:700;'>⚠ IA discrepa</span>"
        else:
            badge = f"<span style='color:{T.MUTED};'>IA: {ia.get('direccion','')}</span>"
        ia_html = (f"<div style='margin-top:6px;border-top:1px solid {T.BORDER};padding-top:6px;"
                   f"font-size:0.82rem;'>🧠 {badge} · {C.esc(ia.get('confianza','—'))}% — "
                   f"{C.esc(ia.get('resumen',''))}</div>")

    s = st.columns([1.8, 1.5, 1.4])
    with s[0]:
        st.markdown(
            f"<div class='gx-card' style='border:2px solid {color};margin-bottom:6px;'>"
            f"<div class='gx-tag'>🎯 Plan consolidado · {symbol.label} · inversión {duration}</div>"
            f"<div style='display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;'>"
            f"<span style='font-size:1.7rem;font-weight:800;color:{color};'>{plan.icon} {plan.action_label}</span>"
            f"<span style='font-size:1.15rem;font-weight:700;'>{plan.confidence:.0f}%</span>"
            f"<span style='font-size:0.85rem;color:{T.MUTED};'>{venc}</span></div>{_sent}{_acc}{_risk_html}{ia_html}</div>",
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
        try:
            _lv = _levels_cached(sk, interval, limit)
        except Exception:
            _lv = None
        st.plotly_chart(
            C.pro_chart(symbol.label, df, sig.support, sig.resistance,
                        show_ma=st.session_state.get("show_ma", True),
                        show_bb=st.session_state.get("show_bb", True),
                        show_volume=st.session_state.get("show_vol", True),
                        levels=_lv),
            use_container_width=True, config=cfg)
    if st.session_state.get("show_ind", True):
        st.plotly_chart(C.indicator_panel(df), use_container_width=True,
                        config={"displayModeBar": False})


def render_details():
    """Detalle bajo el gráfico: RSI/MACD (en stream), lectura, registro y noticias."""
    if not is_authenticated():
        return
    sk = st.session_state["symbol_key"]
    cur = st.session_state.get("_cur") or {}

    # En modo stream el gráfico es JS (sin panel de indicadores) -> lo añadimos aquí
    if st.session_state.get("chart_type") == "🔴 Stream en vivo" \
            and st.session_state.get("show_ind", True):
        try:
            _dfp = load_market(sk, st.session_state["interval"],
                               st.session_state.get("limit", 200))
            st.plotly_chart(C.indicator_panel(_dfp), use_container_width=True,
                            config={"displayModeBar": False})
        except Exception:
            pass

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

        # Resultado REAL de la última señal (el sistema aprende de aciertos/fallos)
        st.markdown("<div class='gx-tag' style='margin-top:6px;'>¿Resultado real?</div>",
                    unsafe_allow_html=True)
        rb = st.columns(2)
        if rb[0].button("✅ Acerté", use_container_width=True):
            tracker.mark_last(sk, True)
            st.success("Marcado como acierto.")
        if rb[1].button("❌ Fallé", use_container_width=True):
            tracker.mark_last(sk, False)
            st.warning("Marcado como fallo: el sistema lo tendrá en cuenta.")
    with d3:
        try:
            st.markdown(C.news_html(load_news(sk)), unsafe_allow_html=True)
        except Exception:
            pass
        try:
            _ev = _macro_cached().get("events", [])
        except Exception:
            _ev = []
        if _ev:
            rows = "".join(
                f"<div class='gx-news'><b>{e['date']}</b> · {e['country']} · {e['event']} "
                f"{'🔴' * e['importance']}</div>" for e in _ev[:6])
            st.markdown(f"<div class='gx-card'><div class='gx-tag'>📅 Calendario económico</div>"
                        f"{rows}</div>", unsafe_allow_html=True)


def _side_refresh(symbol) -> int:
    if symbol.type == "forex":
        return max(15, st.session_state.get("refresh", 5))   # protege cuota Twelve Data
    if symbol.type == "stock":
        return max(8, st.session_state.get("refresh", 5))
    return max(3, st.session_state.get("refresh", 5))         # cripto


def render_qa():
    """Consultas al sistema: responde con lo que HA APRENDIDO (sin IA). Al corregir,
    la IA procesa la corrección y la guarda para aplicarla en el futuro."""
    if not is_authenticated():
        return
    from db import cloud as _cloud
    st.markdown("---")
    st.markdown("### 💬 Pregúntale al sistema")
    st.caption("Responde con lo que ha aprendido. Si lo corriges, la IA procesa tu "
               "corrección, la guarda en Supabase y la aplica en el futuro.")
    sk = st.session_state["symbol_key"]
    q = st.text_input("Tu pregunta", key="qa_q",
                      placeholder="¿Qué has aprendido de EUR/USD? ¿Cómo leo este RSI?")
    if st.button("Preguntar", key="qa_ask") and q.strip():
        # Respuesta SOLO desde lo aprendido (búsqueda en la base de conocimiento)
        hits = _cloud.knowledge_search(q, 3)
        if hits:
            partes = []
            for h in hits:
                _src = h.get("source", "")
                _sum = (h.get("summary") or "").strip()
                if _sum:
                    partes.append(f"- {_sum[:500]}" + (f"  _(fuente: {_src})_" if _src else ""))
            ans = "Según lo que he aprendido:\n\n" + "\n\n".join(partes)
        else:
            ans = ("Todavía no he aprendido nada específico sobre eso. Enséñame con el "
                   "recuadro de abajo y lo recordaré para la próxima.")
        hist = st.session_state.setdefault("qa_hist", [])
        hist.insert(0, {"id": f"{datetime.now().timestamp()}", "q": q.strip(), "a": ans})
        del hist[10:]

    for qa in st.session_state.get("qa_hist", []):
        with st.container(border=True):
            st.markdown(f"**🧑 Tú:** {qa['q']}")
            st.markdown(f"**🧠 Sistema (aprendido):** {qa['a']}")
            with st.expander("✍️ Corregir / afinar (la IA lo procesa y el sistema lo aprende)"):
                corr = st.text_area("Tu corrección o matiz", key=f"qa_corr_{qa['id']}",
                                    label_visibility="collapsed")
                if st.button("Enseñar al sistema", key=f"qa_teach_{qa['id']}") and corr.strip():
                    leccion = corr.strip()
                    if llm.is_available():
                        with st.spinner("La IA procesa tu corrección…"):
                            try:
                                leccion = llm.learn_from_correction(qa["q"], qa["a"], corr.strip())
                            except Exception:
                                leccion = corr.strip()
                    try:
                        dest = _cloud.knowledge_save(
                            "leccion", f"chat:{SYMBOLS_BY_KEY[sk].label}", 0.0,
                            f"{leccion}\n\n(Consulta original: {qa['q']})", "")
                        st.success(f"✅ Aprendido (guardado en {dest}). Lo aplicaré en próximas "
                                   "respuestas y análisis.")
                    except Exception:
                        st.error("No se pudo guardar la corrección ahora.")


with tab_live:
    render_toolbar()
    _symbol = SYMBOLS_BY_KEY[st.session_state["symbol_key"]]
    _ctype = st.session_state.get("chart_type", CHART_TYPES[0])
    _live = st.session_state.get("live", True)
    # La gráfica rica (SMA, Bollinger, niveles, zoom) ahora es para TODOS los mercados
    _stream = _ctype == "🔴 Stream en vivo"
    _strip_refresh = _side_refresh(_symbol) if _live else None

    # Franja superior de avisos (auto-refresca sin reiniciar el gráfico)
    st.fragment(run_every=_strip_refresh)(render_strip)()

    # Gráfico a pantalla completa
    if _stream:
        try:
            _slv = _levels_cached(_symbol.key, st.session_state["interval"], 200)
        except Exception:
            _slv = None
        if _symbol.type == "cripto":
            # Cripto: tick a tick por WebSocket de Binance
            components.html(stream_chart_html(_symbol.provider_id, st.session_state["interval"],
                                              560, levels=_slv, use_ws=True), height=624)
        else:
            # Forex/acciones/índices/materias: MISMA gráfica con todas las herramientas,
            # sembrada con nuestras velas (sin auto-refresco para conservar el zoom).
            _seed = []
            try:
                _dfc = load_market(_symbol.key, st.session_state["interval"],
                                   st.session_state.get("limit", 200))
                _seed = [{"time": int(t.timestamp()), "open": float(o), "high": float(h),
                          "low": float(lo), "close": float(c)}
                         for t, o, h, lo, c in zip(_dfc.index, _dfc["open"], _dfc["high"],
                                                   _dfc["low"], _dfc["close"])]
            except Exception:
                pass
            components.html(stream_chart_html(_symbol.provider_id, st.session_state["interval"],
                                              560, levels=_slv, use_ws=False, seed=_seed),
                            height=624)
    else:
        if not is_realtime(_symbol):
            if st.button("🔄 Actualizar"):
                load_market.clear()
            _chart_refresh = None
        elif _live:
            _seconds = _ctype in ("Velas 5s", "Velas 30s", "Línea en vivo")
            if _symbol.type == "cripto":
                _chart_refresh = 2 if _seconds else st.session_state.get("refresh", 5)
            elif _symbol.type == "forex":
                _chart_refresh = max(15, st.session_state.get("refresh", 5))
            else:
                _chart_refresh = st.session_state.get("refresh", 5)
        else:
            _chart_refresh = None
        st.fragment(run_every=_chart_refresh)(render_chart_full)()

    # Detalle inferior (auto-refresca)
    st.fragment(run_every=_strip_refresh)(render_details)()

    # Consultas al sistema con aprendizaje por retroalimentación (fuera de auto-refresco)
    render_qa()



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
            # Mejor oportunidad por activo, ordenadas por confianza, con veredicto IA
            best = {}
            for r in results:
                if r["symbol"] not in best or r["conf"] > best[r["symbol"]]["conf"]:
                    best[r["symbol"]] = r
            rows = sorted(best.values(), key=lambda r: r["conf"], reverse=True)
            _ia = snap.get("ia", {})
            _l2k = {s.label: s.key for s in SYMBOLS}

            def _ia_badge(r):
                v = _ia.get(_l2k.get(r["symbol"], ""))
                if not v:
                    return "—"
                if r["dir"] in ("SUBE", "BAJA") and v["dir"] == r["dir"]:
                    return f"✓ confirma {v['conf']}%"
                if r["dir"] in ("SUBE", "BAJA") and v["dir"] in ("SUBE", "BAJA"):
                    return f"⚠ discrepa {v['conf']}%"
                return f"IA: {v['dir']}"

            table = [{"Activo": r["symbol"], "Señal": f"{r['icon']} {r['action']}",
                      "Duración": r["dur"], "Confianza %": r["conf"],
                      "IA": _ia_badge(r), "Precio": r["price"], "Hora": r["t"]} for r in rows]
            st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
            st.caption("La columna **IA** muestra el veredicto del cerebro (Gemini/DeepSeek) "
                       "para las señales fuertes: ✓ confirma o ⚠ discrepa de la técnica.")
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


# ============================== TAB: PRECISIÓN =============================
with tab_prec:
    st.subheader("🎯 Precisión del sistema — aprende de aciertos y fallos")
    st.caption("Cada señal se evalúa con el precio REAL al vencer su duración. Esta "
               "precisión retroalimenta la confianza del motor para mejorar con el tiempo.")
    import pandas as pd
    g = tracker.stats()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Señales evaluadas", g["n"])
    m2.metric("Aciertos", g["wins"])
    m3.metric("Fallos", g["losses"])
    m4.metric("Precisión global", f"{g['accuracy']:.0f}%")

    def _style_perf(row):
        """Verde si rinde bien, rojo si falla más que acierta (con muestra mínima)."""
        tot = row.get("Total", 0)
        p = row.get("Precisión %", 0)
        if tot >= 3 and p < 50:
            css = "background-color:rgba(225,29,72,0.14);color:#9f1239;font-weight:600;"
        elif tot >= 3 and p >= 60:
            css = "background-color:rgba(21,163,74,0.14);color:#14532d;font-weight:600;"
        else:
            css = ""
        return [css] * len(row)

    def _insight(label, items, min_n=5):
        """Lectura: mejor y peor categoría con muestra suficiente."""
        elig = [(k, v) for k, v in items if v["total"] >= min_n]
        if not elig:
            return None
        best = max(elig, key=lambda x: x[1]["precisión"])
        worst = min(elig, key=lambda x: x[1]["precisión"])
        msg = f"**{label}** — mejor: **{best[0]}** ({best[1]['precisión']:.0f}%)"
        if worst[0] != best[0]:
            msg += f" · evitar: **{worst[0]}** ({worst[1]['precisión']:.0f}%)"
        return msg

    cv = tracker.curve()
    if cv:
        st.markdown("#### Evolución de la precisión")
        st.line_chart(pd.DataFrame(cv).set_index("señal"))

        # ---- Rendimiento POR MERCADO (Forex, Cripto, Acciones, Índices, Materias) ----
        _CAT = ["Forex", "Cripto", "Acciones", "Índices", "Materias"]
        gm: dict = {}
        for _s in tracker.evaluated():
            _sym = _s.get("symbol")
            _grp = SYMBOLS_BY_KEY[_sym].group if _sym in SYMBOLS_BY_KEY else "Otros"
            _a = gm.setdefault(_grp, {"aciertos": 0, "total": 0})
            _a["total"] += 1
            if _s.get("status") == "win":
                _a["aciertos"] += 1
        for _v in gm.values():
            _v["precisión"] = round(100 * _v["aciertos"] / _v["total"], 1) if _v["total"] else 0.0

        bs = tracker.breakdown_symbol()
        bd = tracker.breakdown_duration()

        # Lectura estructurada para el asesor (con muestra mínima fiable)
        lect = []
        _mk = _insight("Mercado", list(gm.items()), min_n=4)
        _ms = _insight("Activos", [(SYMBOLS_BY_KEY[k].label if k in SYMBOLS_BY_KEY else k, v)
                                   for k, v in bs.items()])
        _md = _insight("Duraciones", list(bd.items()))
        for _x in (_mk, _ms, _md):
            if _x:
                lect.append(_x)
        if lect:
            st.success("🧭 Lectura del asesor → " + "  ·  ".join(lect))
        else:
            st.caption("🧭 Acumula al menos 5 resultados por categoría para una lectura fiable.")

        st.markdown("#### 🌐 Por mercado — ¿dónde se gana más fácil?")
        if gm:
            mk1, mk2 = st.columns([1.1, 1])
            with mk1:
                rows = [{"Mercado": k, "Aciertos": v["aciertos"],
                         "Fallos": v["total"] - v["aciertos"], "Total": v["total"],
                         "Precisión %": v["precisión"]}
                        for k, v in sorted(gm.items(), key=lambda x: -x[1]["precisión"])]
                st.dataframe(pd.DataFrame(rows).style.apply(_style_perf, axis=1),
                             use_container_width=True, hide_index=True)
            with mk2:
                st.bar_chart(pd.Series({k: v["precisión"] for k, v in gm.items()},
                                       name="Precisión %"))
        _missing = [c for c in _CAT if c not in gm]
        if _missing:
            st.caption("Sin datos todavía en: **" + ", ".join(_missing) + "**. Se registran "
                       "cuando el motor autónomo corre (con la página abierta) y en horario "
                       "de ese mercado (el Forex y las acciones cierran fines de semana).")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Por activo")
            if bs:
                rows = [{"Activo": SYMBOLS_BY_KEY[k].label if k in SYMBOLS_BY_KEY else k,
                         "Aciertos": v["aciertos"], "Fallos": v["total"] - v["aciertos"],
                         "Total": v["total"], "Precisión %": v["precisión"]}
                        for k, v in sorted(bs.items(), key=lambda x: -x[1]["precisión"])]
                st.dataframe(pd.DataFrame(rows).style.apply(_style_perf, axis=1),
                             use_container_width=True, hide_index=True)
        with c2:
            st.markdown("#### Por duración")
            if bd:
                rows = [{"Duración": k, "Aciertos": v["aciertos"],
                         "Fallos": v["total"] - v["aciertos"], "Total": v["total"],
                         "Precisión %": v["precisión"]}
                        for k, v in sorted(bd.items(), key=lambda x: -x[1]["precisión"])]
                st.dataframe(pd.DataFrame(rows).style.apply(_style_perf, axis=1),
                             use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay señales evaluadas. Enciende **🤖 Autónomo 24/7** y deja correr "
                "el sistema; cuando venzan las señales aparecerá aquí su rendimiento.")

    if st.button("🗑️ Reiniciar historial de precisión"):
        tracker.reset()
        st.success("Historial reiniciado.")


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
                    titles = [i.title for i in digest.items]
                    label = SYMBOLS_BY_KEY[sk].label
                    # Contexto extra para el cerebro: sentimiento social + macro
                    _ex = []
                    _so = _social_cached(sk)
                    if _so:
                        _ex.append(f"Sentimiento social: {_so['label']} ({_so['detail']}).")
                    try:
                        _mc = _macro_cached().get("events", [])[:3]
                        if _mc:
                            _ex.append("Eventos macro próximos: " +
                                       "; ".join(f"{e['event']} ({e['country']})" for e in _mc))
                    except Exception:
                        pass
                    try:
                        _ex.append(snapshot_text(df))
                    except Exception:
                        pass
                    extra = "  ".join(x for x in _ex if x)
                    # Resultado ESTRUCTURADO (JSON) y, debajo, explicación en prosa
                    try:
                        v = llm.structured_verdict(sig, label, titles, extra_context=extra)
                        # Alimenta el sistema: guarda el análisis del activo en el conocimiento
                        try:
                            from db import cloud as _cloud
                            _cloud.knowledge_save(
                                "analisis", f"analisis:{label}", 0.0,
                                f"Veredicto IA {label}: {v.get('direccion','')} "
                                f"({v.get('confianza','')}%). {v.get('resumen','')} "
                                f"Riesgos: {v.get('riesgos','')}", extra)
                        except Exception:
                            pass
                        col = T.GREEN if v.get("direccion") == "COMPRA" else \
                            T.RED if v.get("direccion") == "VENTA" else T.GOLD
                        st.markdown(
                            f"<div class='gx-card' style='border:2px solid {col};'>"
                            f"<div class='gx-tag'>Veredicto IA · {C.esc(label)}</div>"
                            f"<div style='font-size:1.5rem;font-weight:800;color:{col};'>"
                            f"{C.esc(v.get('direccion','—'))} · {C.esc(v.get('confianza','—'))}%</div>"
                            f"<div style='margin-top:6px;'>{C.esc(v.get('resumen',''))}</div>"
                            f"<div style='margin-top:6px;color:{T.MUTED};'>⚠️ {C.esc(v.get('riesgos',''))}</div>"
                            + (f"<div style='margin-top:4px;color:{T.MUTED};'>Niveles: "
                               f"{C.esc(v.get('niveles_clave',''))}</div>" if v.get('niveles_clave') else "")
                            + "</div>", unsafe_allow_html=True)
                    except Exception:
                        st.markdown(llm.reason_trade(sig, label, titles, extra_context=extra))
                except Exception:  # noqa: BLE001 — sin exponer claves
                    st.error("La IA está al límite ahora mismo (Gemini sin cuota y el "
                             "respaldo DeepSeek no respondió: revisa su saldo/clave). "
                             "El sistema y el resto de pestañas siguen funcionando; "
                             "vuelve a intentarlo en un momento.")

    with c_ingest:
        st.markdown("#### 📥 Procesar contenido que le adjuntes")
        kind = st.radio("Tipo", ["Texto", "YouTube (URL)"], horizontal=True,
                        label_visibility="collapsed")
        if kind == "Texto":
            txt = st.text_area("Pega aquí un artículo, notas o estrategia", height=160)
            if st.button("Analizar contenido"):
                if not (txt or "").strip():
                    st.warning("Pega primero algún texto para enseñarle al cerebro.")
                else:
                    with st.spinner("Guardando y analizando..."):
                        try:
                            res = ingest.ingest_text(txt)
                            st.success(f"✅ Conocimiento guardado en **{res.saved}**.")
                            st.caption(f"Sentimiento: {res.sentiment:+.2f}")
                            st.markdown(res.analysis)
                        except Exception as e:  # noqa: BLE001
                            st.error(f"Error: {e}")
        else:
            url = st.text_input("URL de YouTube", placeholder="https://youtu.be/...")
            st.caption("Se analiza la **transcripción** (lo que se dice), no la imagen.")
            if st.button("Analizar video"):
                if not (url or "").strip():
                    st.warning("Pega primero la URL del video.")
                else:
                    with st.spinner("Bajando transcripción, guardando y analizando..."):
                        try:
                            res = ingest.ingest_youtube(url)
                            st.success(f"✅ Conocimiento guardado en **{res.saved}**.")
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
    st.caption("Tres formas de aprender, todas APOYO probabilístico, no garantías.")

    # ---- Aprendizaje de TUS resultados reales (sin que marques nada) ----
    from analysis import self_learn
    st.markdown("### 🧠 Aprende de los resultados reales (automático)")
    st.write("Cada señal se guarda con su foto de indicadores y, al vencer, se marca "
             "ACIERTO/FALLO con el precio real. El modelo aprende de ESO para estimar la "
             "probabilidad de acierto y ajustar la confianza del plan. No tienes que hacer nada.")
    _sl = self_learn.stats()
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Resultados con datos", _sl["n"])
    s2.metric("Aciertos", _sl["wins"])
    s3.metric("Tasa de acierto", f"{_sl['win_rate']:.0f}%")
    s4.metric("Precisión del modelo", f"{_sl['accuracy']:.0f}%" if _sl["trained_n"] else "—")
    if _sl["n"] < self_learn.MIN_SAMPLES:
        st.info(f"Acumulando experiencia: {_sl['n']}/{self_learn.MIN_SAMPLES} resultados. "
                "Deja el sistema corriendo (motor autónomo encendido) y, cuando haya "
                "suficientes, empezará a aprender solo.")
    else:
        if st.button("🧠 Entrenar ahora con resultados reales"):
            with st.spinner("Aprendiendo de tu historial real…"):
                rep = self_learn.train()
            if rep.get("ok"):
                st.success(f"Aprendido de {rep['n']} resultados · precisión "
                           f"**{rep['accuracy']:.0%}** · aciertos {rep['win_rate']:.0f}%.")
                import pandas as pd
                st.caption("Qué indicadores pesan más para acertar")
                st.bar_chart(pd.Series(rep["importances"]))
            else:
                st.warning(rep.get("msg", "Aún no se puede entrenar."))
        if self_learn.is_ready():
            st.caption("✅ El modelo de resultados reales está activo y ajustando la confianza.")

    st.divider()
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
