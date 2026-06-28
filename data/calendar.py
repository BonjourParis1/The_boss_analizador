"""
data/calendar.py — Calendario de eventos (earnings) para proteger el capital.

Las mayores sacudidas del mercado ocurren por eventos, no por análisis técnico.
Esta utilidad avisa si una ACCIÓN tiene reporte de resultados (earnings) próximo,
para que el sistema sea prudente cerca de esas fechas. Requiere FINNHUB_API_KEY.
"""
from __future__ import annotations

from datetime import date, timedelta

import requests

from config import Symbol, settings

_TIMEOUT = 8
_HEADERS = {"User-Agent": "GuiaExpertoTrading/2.0"}


def earnings_soon(symbol: Symbol, days: int = 2) -> str | None:
    """Devuelve la fecha (ISO) del próximo reporte si cae dentro de `days` días.

    Solo aplica a acciones y si hay clave de Finnhub. None en cualquier otro caso.
    """
    if symbol.type != "stock" or not settings.finnhub_api_key:
        return None
    try:
        today = date.today()
        r = requests.get("https://finnhub.io/api/v1/calendar/earnings", timeout=_TIMEOUT,
                         headers=_HEADERS,
                         params={"from": today.isoformat(),
                                 "to": (today + timedelta(days=days)).isoformat(),
                                 "symbol": symbol.provider_id,
                                 "token": settings.finnhub_api_key})
        r.raise_for_status()
        items = r.json().get("earningsCalendar") or []
        return items[0]["date"] if items else None
    except Exception:
        return None
