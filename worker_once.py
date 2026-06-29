"""
worker_once.py — UNA pasada del motor autónomo y termina.

Pensado para ejecutarse de forma programada (cron, GitHub Actions) cada pocos minutos:
analiza todos los activos, registra señales fuertes, evalúa las vencidas con el precio
real y guarda todo en Supabase. Es la opción GRATIS para tener "24/7" sin un servidor
encendido (mientras el programador lo dispare).

Arranque:
    python worker_once.py
"""
from __future__ import annotations

import os
import threading
from datetime import datetime, timezone


def main() -> None:
    from config import settings
    from autonomous import _scan_cycle

    stop = threading.Event()  # nunca se activa: una sola pasada
    min_conf = float(os.getenv("AUTO_MIN_CONFIDENCE", "65"))
    timeframe = os.getenv("AUTO_TIMEFRAME", "5m")
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{now}] pasada única · Supabase={'sí' if settings.use_supabase else 'NO'}", flush=True)
    found = _scan_cycle(stop, min_conf, timeframe)
    print(f"[{now}] ✅ {found} señal(es) fuerte(s); señales/resultados guardados.", flush=True)


if __name__ == "__main__":
    main()
