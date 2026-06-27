"""
scanner.py — Escáner autónomo 24/7 (proceso independiente del dashboard).

Recorre TODOS los activos cada N minutos, calcula la señal del experto (técnico +
patrones de velas + sentimiento de noticias), guarda las recomendaciones en la base
de datos y, si hay señales fuertes, envía aviso por correo (si está activado).

Pensado para dejarlo corriendo aparte del dashboard:
    python scanner.py                 # bucle continuo
    python scanner.py --once          # una sola pasada (útil para cron/pruebas)
    python scanner.py --min-confidence 70

Así el sistema "trabaja solo" aunque no tengas el navegador abierto.
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime

# Salida UTF-8 en consolas Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from analysis import advisor, auto_learn
from analysis.engine import BUY, SELL, analyze
from analysis.indicators import compute_all
from analysis.news import get_news
from analysis.patterns import read_candles
from config import SYMBOLS, settings
from data.connectors import fetch_with_retry
from db.store import BACKEND, init_db, save_recommendation
from notifications import email_alerts


def _log(msg: str) -> None:
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def scan_once(interval: str = "5m", min_confidence: float = 65.0) -> list:
    """Una pasada por todos los activos. Devuelve las señales fuertes encontradas."""
    strong = []
    for s in SYMBOLS:
        try:
            df = compute_all(fetch_with_retry(s, interval=interval, limit=150))
            reading = read_candles(df)
            try:
                news = get_news(s)
                news_score = news.score
                titles = [i.title for i in news.items]
            except Exception:
                news_score, titles = None, []
            sig = analyze(s.key, df, news_score=news_score, candles=reading)

            if sig.action in (BUY, SELL) and sig.confidence >= min_confidence:
                save_recommendation(sig)
                strong.append((s, sig))
                ap = ac = None
                if auto_learn.model_exists():
                    try:
                        ap, ac, _ = auto_learn.predict(df)
                    except Exception:
                        pass
                plan = advisor.build_plan(sig, ap, ac)
                _log(f"⚡ {plan.icon} {plan.action_label} {s.label} · "
                     f"{plan.duration_label} · conf={plan.confidence:.0f}% · precio={sig.price}")
                if email_alerts.is_enabled():
                    ok, info = email_alerts.send_signal_alert(sig, s.label)
                    _log(f"   correo: {info}")
        except Exception as e:  # noqa: BLE001
            _log(f"   (sin datos {s.label}: {e})")
        time.sleep(1.0)  # cortesía con las APIs
    return strong


def main() -> None:
    p = argparse.ArgumentParser(description="Escáner autónomo de mercado.")
    p.add_argument("--once", action="store_true", help="Una sola pasada y salir.")
    p.add_argument("--interval", default="5m", help="Temporalidad (1m,5m,15m,1h,1d).")
    p.add_argument("--min-confidence", type=float, default=65.0)
    args = p.parse_args()

    init_db()
    every = max(1, settings.scan_interval_minutes)
    _log(f"Escáner iniciado · backend={BACKEND} · {len(SYMBOLS)} activos · "
         f"cada {every} min · confianza≥{args.min_confidence}%")

    while True:
        n = len(scan_once(args.interval, args.min_confidence))
        _log(f"Pasada completa. Señales fuertes: {n}")
        if args.once:
            break
        time.sleep(every * 60)


if __name__ == "__main__":
    main()
