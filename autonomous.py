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

from analysis import advisor, auto_learn
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


_S = _State()


def _scan_cycle(stop_event: threading.Event, min_conf: float, timeframe: str) -> int:
    found = 0
    has_model = auto_learn.model_exists()
    for s in SYMBOLS:
        if stop_event.is_set():
            break
        try:
            df = compute_all(fetch_with_retry(s, interval=timeframe, limit=150))
            sig = analyze(s.key, df, candles=read_candles(df))
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
        # Espera hasta el siguiente ciclo, comprobando parada cada segundo
        waited = 0
        while waited < interval_s and not stop_event.is_set():
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
        }
