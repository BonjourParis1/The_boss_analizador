"""
data/normalizer.py — Normalización al formato JSON solicitado:
    {timestamp, symbol, price, volume}
Útil para registrar ticks, enviar a colas o auditar.
"""
from __future__ import annotations

import pandas as pd


def latest_tick(symbol_key: str, df: pd.DataFrame) -> dict:
    """Devuelve el último punto como dict JSON-serializable."""
    last = df.iloc[-1]
    return {
        "timestamp": df.index[-1].isoformat(),
        "symbol": symbol_key,
        "price": float(last["close"]),
        "volume": float(last.get("volume", 0.0)),
    }


def to_json_records(symbol_key: str, df: pd.DataFrame) -> list[dict]:
    """Convierte toda la serie al formato normalizado."""
    out = []
    for ts, row in df.iterrows():
        out.append({
            "timestamp": ts.isoformat(),
            "symbol": symbol_key,
            "price": float(row["close"]),
            "volume": float(row.get("volume", 0.0)),
        })
    return out
