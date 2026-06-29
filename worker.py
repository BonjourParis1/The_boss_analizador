"""
worker.py — Motor autónomo 24/7 como proceso INDEPENDIENTE (sin Streamlit).

Pensado para un servicio "background worker" (Render, Railway, Fly.io o un VPS) que
está SIEMPRE encendido. Ejecuta el mismo análisis que el motor interno del dashboard,
pero en su propio proceso, así el sistema aprende y registra señales aunque no tengas
la página abierta. Todo se guarda en Supabase (datos en la nube), de donde el dashboard
lo lee y muestra.

Arranque:
    python worker.py

Variables de entorno (las mismas del dashboard): SUPABASE_URL, SUPABASE_SERVICE_KEY,
LLM_PROVIDER=gemini, GEMINI_API_KEY, DEEPSEEK_API_KEY, FINNHUB_API_KEY,
TWELVEDATA_API_KEY, ALPHA_VANTAGE_API_KEY, SCAN_INTERVAL_MINUTES.
"""
from __future__ import annotations

import os
import signal
import threading
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


def main() -> None:
    from config import settings
    from autonomous import _scan_cycle

    stop = threading.Event()
    for _sig in (getattr(signal, "SIGTERM", None), getattr(signal, "SIGINT", None)):
        if _sig is not None:
            try:
                signal.signal(_sig, lambda *_: stop.set())
            except Exception:
                pass

    interval = max(60, int(settings.scan_interval_minutes) * 60)
    min_conf = float(os.getenv("AUTO_MIN_CONFIDENCE", "65"))
    timeframe = os.getenv("AUTO_TIMEFRAME", "5m")
    print(f"[{_now()}] 🤖 worker 24/7 iniciado · cada {interval}s · conf≥{min_conf:.0f}% · "
          f"Supabase={'sí' if settings.use_supabase else 'NO (local)'}", flush=True)

    while not stop.is_set():
        try:
            found = _scan_cycle(stop, min_conf, timeframe)
            print(f"[{_now()}] pasada completa · {found} señal(es) fuerte(s)", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[{_now()}] error en la pasada: {e}", flush=True)
        waited = 0
        while waited < interval and not stop.is_set():
            stop.wait(1)
            waited += 1

    print(f"[{_now()}] ⏹ worker detenido", flush=True)


if __name__ == "__main__":
    main()
