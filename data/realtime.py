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

from config import Symbol

_TIMEOUT = 6
_HEADERS = {"User-Agent": "GuiaExpertoTrading/2.0"}


def is_realtime(symbol: Symbol) -> bool:
    """Solo cripto tiene streaming real gratuito."""
    return symbol.type == "cripto"


def fast_quote(symbol: Symbol) -> dict | None:
    """Cotización rápida para el ticker. None si no hay fuente en vivo."""
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
