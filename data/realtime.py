"""
data/realtime.py — Precio en tiempo real (tick a tick) para el encabezado.

* Criptomonedas: endpoint ligero de Binance /ticker/24hr -> precio y % 24h.
  Es muy barato, así que se puede consultar cada 1-2 segundos (sensación "en vivo").
* Forex/acciones: NO hay fuente gratuita tick a tick fiable. Alpha Vantage (gratis)
  permite solo ~25 llamadas/día, así que esos mercados NO se auto-refrescan a alta
  frecuencia: se actualizan con el botón "Actualizar" o al cambiar de activo.

Devuelve un dict {price, change, change_pct, is_live}.
"""
from __future__ import annotations

import requests

from config import Symbol, settings

_TIMEOUT = 6
_HEADERS = {"User-Agent": "GuiaExpertoTrading/2.0"}


def is_realtime(symbol: Symbol) -> bool:
    """Cripto siempre (Binance); acciones si hay Finnhub configurado."""
    if symbol.type == "cripto":
        return True
    if symbol.type == "stock" and settings.finnhub_api_key:
        return True
    return False


def _finnhub_quote(symbol: Symbol) -> dict | None:
    """Precio en vivo de acciones US vía Finnhub (free 60/min)."""
    try:
        r = requests.get("https://finnhub.io/api/v1/quote",
                         params={"symbol": symbol.provider_id,
                                 "token": settings.finnhub_api_key},
                         headers=_HEADERS, timeout=_TIMEOUT)
        r.raise_for_status()
        d = r.json()
        if not d.get("c"):
            return None
        return {"price": float(d["c"]), "change": float(d.get("d") or 0.0),
                "change_pct": float(d.get("dp") or 0.0), "high": float(d.get("h") or 0.0),
                "low": float(d.get("l") or 0.0), "volume": 0.0, "is_live": True}
    except Exception:
        return None


def fast_quote(symbol: Symbol) -> dict | None:
    """Cotización rápida para el ticker. None si no hay fuente en vivo."""
    if symbol.type == "stock" and settings.finnhub_api_key:
        return _finnhub_quote(symbol)
    if symbol.type != "cripto":
        return None
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/24hr",
                         params={"symbol": symbol.provider_id},
                         headers=_HEADERS, timeout=_TIMEOUT)
        r.raise_for_status()
        d = r.json()
        return {
            "price": float(d["lastPrice"]),
            "change": float(d["priceChange"]),
            "change_pct": float(d["priceChangePercent"]),
            "high": float(d["highPrice"]),
            "low": float(d["lowPrice"]),
            "volume": float(d["volume"]),
            "is_live": True,
        }
    except Exception:
        return None
