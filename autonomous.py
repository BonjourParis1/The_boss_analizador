"""
autonomous.py — Motor autónomo en segundo plano (dentro del dashboard).

Lanza un hilo que analiza TODOS los mercados en bucle y va generando planes de
operación (COMPRA/VENTA/ESPERAR + duración). El dashboard lo arranca al iniciar y
puede DETENERLO en cualquier momento para descansar y no gastar recursos.

Diseño:
  * El hilo NO llama a Streamlit (solo calcula y guarda en una estructura compartida
    protegida por lock), así que es seguro y no rompe la sesión.
  * `stop()` lo detiene en ~1 segundo y el hilo termina por completo -> 0 CPU al parar.
  * Es un singleton a nivel de proceso (persiste entre reruns de Streamlit).
"""
from __future__ import annotations

import threading
import time
from collections import deque
from datetime import datetime

from analysis import advisor, auto_learn, tracker
from analysis.engine import analyze
from analysis.indicators import compute_all
from analysis.patterns import read_candles
from config import SYMBOLS
from data.connectors import fetch_with_retry
from db.store import save_recommendation


class _State:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.running = False
        self.results: deque = deque(maxlen=80)   # operaciones sugeridas (todos los activos)
        self.log: deque = deque(maxlen=15)
        self.last_scan: datetime | None = None
        self.cycles = 0
        self.found_total = 0
        self.interval_seconds = 300
        self.min_confidence = 65.0
        self.timeframe = "5m"
        # Auto-investigación de señales fuertes (contexto de noticias/YouTube)
        self.research: dict = {}          # symbol_key -> {t, label, action, text}
        self._research_cooldown: dict = {}  # symbol_key -> epoch del último estudio
        self.ia: dict = {}                # symbol_key -> {dir, conf, resumen} (veredicto IA)
        self.forex_focus = True           # priorizar Forex (y rotar el resto de mercados)


_S = _State()


_RESEARCH_COOLDOWN_S = 900   # no reinvestigar el mismo activo en 15 min
_MAX_RESEARCH_PER_CYCLE = 2  # acota el tiempo del ciclo (la IA puede ser lenta)
_OTHERS_PER_CYCLE = 4        # cuántos activos de "otros mercados" se rotan por pasada


def _scan_targets():
    """Lista de activos a analizar esta pasada.

    Modo Foco Forex: SIEMPRE todos los pares de Forex (prioridad para la cuota de
    datos) + todo el Cripto (gratis por Binance, 24/7), y ROTA los demás mercados
    (acciones, índices, materias) unos pocos por pasada, para cubrirlos sin agotar
    las APIs gratuitas. Si se desactiva, analiza todos los activos cada pasada.
    """
    if not _S.forex_focus:
        return list(SYMBOLS)
    forex = [s for s in SYMBOLS if s.group == "Forex"]
    cripto = [s for s in SYMBOLS if s.group == "Cripto"]
    otros = [s for s in SYMBOLS if s.group not in ("Forex", "Cripto")]
    rot = []
    if otros:
        start = (_S.cycles * _OTHERS_PER_CYCLE) % len(otros)
        rot = [otros[(start + i) % len(otros)] for i in range(min(_OTHERS_PER_CYCLE, len(otros)))]
    return forex + cripto + rot


def set_forex_focus(enabled: bool) -> None:
    with _S.lock:
        _S.forex_focus = bool(enabled)


def _forex_open() -> bool:
    """Aproxima el horario del Forex (abre dom ~21:00 UTC, cierra vie ~21:00 UTC)."""
    now = datetime.utcnow()
    wd = now.weekday()  # 0=lun … 6=dom
    if wd == 5:            # sábado: cerrado
        return False
    if wd == 6:            # domingo: abre ~21:00 UTC
        return now.hour >= 21
    if wd == 4:            # viernes: cierra ~21:00 UTC
        return now.hour < 21
    return True            # lun–jue: abierto


def _effective_interval() -> int:
    """Con Foco Forex y mercado abierto, pasadas más seguidas (60s, respeta 8/min de
    Twelve Data). En otro caso, el intervalo normal configurado."""
    base = int(_S.interval_seconds)
    if _S.forex_focus and _forex_open():
        return max(60, min(base, 60))
    return base


def _maybe_research(symbol, sig, plan, done_count: int) -> int:
    """Verifica una señal fuerte con el cerebro IA (veredicto estructurado) e
    investiga su contexto (noticias/YouTube), con cooldown para no saturar APIs."""
    import time as _t
    if done_count >= _MAX_RESEARCH_PER_CYCLE:
        return done_count
    if _t.time() - _S._research_cooldown.get(symbol.key, 0) < _RESEARCH_COOLDOWN_S:
        return done_count
    text = None
    try:
        from ingest.content import auto_research
        text = auto_research(symbol)
    except Exception:
        pass
    ia = None
    try:
        from brain import llm
        if llm.is_available():
            v = llm.structured_verdict(sig, symbol.label, [], "")
            _m = {"COMPRA": "SUBE", "VENTA": "BAJA", "ESPERAR": "ESPERAR"}
            ia = {"dir": _m.get(str(v.get("direccion", "")).upper(), "ESPERAR"),
                  "conf": v.get("confianza"), "resumen": v.get("resumen", "")}
    except Exception:
        ia = None
    with _S.lock:
        if text:
            _S.research[symbol.key] = {
                "t": datetime.now().strftime("%H:%M:%S"), "label": symbol.label,
                "action": plan.action_label, "icon": plan.icon, "text": text}
        if ia:
            _S.ia[symbol.key] = ia
        _S._research_cooldown[symbol.key] = _t.time()
    return done_count + 1


def _scan_cycle(stop_event: threading.Event, min_conf: float, timeframe: str) -> int:
    found = 0
    researched = 0
    has_model = auto_learn.model_exists()
    for s in _scan_targets():
        if stop_event.is_set():
            break
        try:
            df = compute_all(fetch_with_retry(s, interval=timeframe, limit=150))
            sig = analyze(s.key, df, candles=read_candles(df))
            # Autoevaluación: marca acierto/fallo de señales vencidas con el precio real
            try:
                tracker.evaluate(s.key, float(df["close"].iloc[-1]))
            except Exception:
                pass
            ap = ac = None
            if has_model:
                try:
                    ap, ac, _ = auto_learn.predict(df)
                except Exception:
                    pass
            plan = advisor.build_plan(sig, ap, ac)
            if plan.is_actionable and plan.confidence >= min_conf:
                try:
                    save_recommendation(sig)
                except Exception:
                    pass
                with _S.lock:
                    _S.results.appendleft({
                        "t": datetime.now().strftime("%H:%M:%S"),
                        "symbol": s.label,
                        "dir": plan.direction,
                        "action": plan.action_label,
                        "icon": plan.icon,
                        "dur": plan.duration_label,
                        "conf": round(plan.confidence, 1),
                        "price": sig.price,
                    })
                found += 1
                # Registra la señal CON su foto de indicadores (para autoaprender)
                try:
                    from ml.model import extract_features
                    _feat = extract_features(df)[0].tolist()
                except Exception:
                    _feat = None
                try:
                    tracker.record(s.key, plan.direction, plan.expiry_seconds, sig.price,
                                   "auto", features=_feat)
                except Exception:
                    pass
                # Verificación IA + investigación del contexto de esta señal fuerte
                researched = _maybe_research(s, sig, plan, researched)
        except Exception:
            pass
        # Pausa breve, interrumpible (cortesía con las APIs)
        stop_event.wait(0.4)
    return found


def _loop(stop_event: threading.Event, min_conf: float, timeframe: str, interval_s: int) -> None:
    while not stop_event.is_set():
        found = _scan_cycle(stop_event, min_conf, timeframe)
        with _S.lock:
            _S.last_scan = datetime.now()
            _S.cycles += 1
            _S.found_total += found
            _S.log.appendleft(f"{_S.last_scan:%H:%M:%S} · pasada {_S.cycles}: "
                              f"{found} señal(es)")
        # Espera hasta el siguiente ciclo (más corto si Foco Forex y el mercado abierto)
        eff = _effective_interval()
        waited = 0
        while waited < eff and not stop_event.is_set():
            stop_event.wait(1)
            waited += 1
    with _S.lock:
        _S.running = False
        _S.log.appendleft(f"{datetime.now():%H:%M:%S} · ⏹ detenido (recursos liberados)")


def start(interval_seconds: int = 300, min_confidence: float = 65.0,
          timeframe: str = "5m") -> None:
    """Arranca el motor autónomo si no está corriendo."""
    with _S.lock:
        if _S.running:
            return
        _S.stop_event = threading.Event()
        _S.running = True
        _S.interval_seconds = max(30, int(interval_seconds))
        _S.min_confidence = float(min_confidence)
        _S.timeframe = timeframe
        ev = _S.stop_event
        _S.log.appendleft(f"{datetime.now():%H:%M:%S} · ▶ iniciado "
                          f"(cada {_S.interval_seconds}s, conf≥{min_confidence:.0f}%)")
    t = threading.Thread(target=_loop,
                         args=(ev, min_confidence, timeframe, _S.interval_seconds),
                         daemon=True)
    with _S.lock:
        _S.thread = t
    t.start()


def stop() -> None:
    """Detiene el motor (el hilo termina en ~1s y deja de consumir recursos)."""
    with _S.lock:
        _S.stop_event.set()
        _S.running = False


def is_running() -> bool:
    return _S.running


def snapshot() -> dict:
    with _S.lock:
        return {
            "running": _S.running,
            "last_scan": _S.last_scan,
            "cycles": _S.cycles,
            "found_total": _S.found_total,
            "interval_seconds": _S.interval_seconds,
            "min_confidence": _S.min_confidence,
            "results": list(_S.results),
            "log": list(_S.log),
            "research": list(_S.research.values()),
            "ia": dict(_S.ia),
        }
