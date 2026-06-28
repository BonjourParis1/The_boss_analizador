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


def economic_events(days: int = 2, min_importance: int = 2) -> list[dict]:
    """Próximos eventos macro de ALTO impacto (Fed, CPI, empleo…).

    Usa Trading Economics con acceso gratuito 'guest:guest'. Devuelve una lista de
    {date, country, event, importance}. Las mayores sacudidas del mercado vienen de
    estos anuncios, no del análisis técnico.
    """
    try:
        today = date.today()
        r = requests.get("https://api.tradingeconomics.com/calendar", timeout=_TIMEOUT,
                         headers=_HEADERS,
                         params={"c": "guest:guest", "f": "json",
                                 "d1": today.isoformat(),
                                 "d2": (today + timedelta(days=days)).isoformat()})
        r.raise_for_status()
        out = []
        for e in r.json():
            try:
                imp = int(e.get("Importance") or 0)
            except (TypeError, ValueError):
                imp = 0
            if imp < min_importance:
                continue
            out.append({"date": (e.get("Date") or "")[:16].replace("T", " "),
                        "country": e.get("Country", ""), "event": e.get("Event", ""),
                        "importance": imp})
        out.sort(key=lambda x: x["date"])
        return out[:8]
    except Exception:
        return []


def major_event_soon(hours: int = 12) -> dict | None:
    """Devuelve el próximo evento macro de máximo impacto dentro de `hours` horas."""
    from datetime import datetime
    try:
        now = datetime.utcnow()
        for e in economic_events(days=1, min_importance=3):
            try:
                when = datetime.fromisoformat(e["date"].replace(" ", "T"))
            except Exception:
                continue
            if 0 <= (when - now).total_seconds() <= hours * 3600:
                return e
    except Exception:
        return None
    return None


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
