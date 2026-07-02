"""
analysis/levels.py — Niveles clave que el sistema DIBUJA automáticamente.

Calcula, sin intervención manual:
  * Máximo y mínimo del DÍA, la SEMANA y el MES (los "puntos más altos/bajos").
  * Soporte y resistencia recientes (de analysis.patterns).

Devuelve una lista de niveles {name, value, kind} donde kind ∈ {"res","sup"}
para que el gráfico los pinte (rojo=resistencia/techo, verde=soporte/suelo).
"""
from __future__ import annotations

import pandas as pd

from analysis.patterns import _support_resistance


def _hi_lo(df: pd.DataFrame, days: float):
    """Máximo y mínimo en la ventana de los últimos `days` días."""
    if df is None or df.empty:
        return None, None
    end = df.index[-1]
    win = df[df.index >= end - pd.Timedelta(days=days)]
    if win.empty:
        win = df
    return float(win["high"].max()), float(win["low"].min())


def compute_levels(intraday: pd.DataFrame, daily: pd.DataFrame | None = None) -> list[dict]:
    """Niveles automáticos. `intraday` para el día; `daily` (velas 1d) para semana/mes."""
    levels: list[dict] = []
    base_day = intraday if intraday is not None and not intraday.empty else daily
    src_wm = daily if daily is not None and not daily.empty else intraday

    d_hi, d_lo = _hi_lo(base_day, 1)
    w_hi, w_lo = _hi_lo(src_wm, 7)
    m_hi, m_lo = _hi_lo(src_wm, 30)

    def add(name, val, kind):
        if val is not None:
            levels.append({"name": name, "value": round(float(val), 6), "kind": kind})

    add("Máx día", d_hi, "res")
    add("Mín día", d_lo, "sup")
    add("Máx semana", w_hi, "res")
    add("Mín semana", w_lo, "sup")
    add("Máx mes", m_hi, "res")
    add("Mín mes", m_lo, "sup")

    # Soporte/resistencia recientes (swing highs/lows)
    try:
        sup, res = _support_resistance(intraday)
        add("Resistencia", res, "res")
        add("Soporte", sup, "sup")
    except Exception:
        pass

    # Quitar niveles duplicados muy cercanos (evita amontonar líneas)
    dedup: list[dict] = []
    for lv in levels:
        if all(abs(lv["value"] - o["value"]) / (abs(lv["value"]) + 1e-9) > 0.0008 for o in dedup):
            dedup.append(lv)

    # Dejar SOLO los niveles relevantes al precio actual (gráfico limpio como IQ Option):
    # la resistencia más cercana por encima y el soporte más cercano por debajo, más el
    # máximo/mínimo del día como contexto. Así no se amontonan 8 líneas en el eje.
    try:
        price = float((base_day if base_day is not None and not base_day.empty
                       else src_wm)["close"].iloc[-1])
    except Exception:
        return dedup

    res = sorted([l for l in dedup if l["kind"] == "res" and l["value"] >= price],
                 key=lambda l: l["value"] - price)
    sup = sorted([l for l in dedup if l["kind"] == "sup" and l["value"] <= price],
                 key=lambda l: price - l["value"])
    keep, seen = [], set()
    for name in ("Máx día", "Mín día"):
        for l in dedup:
            if l["name"] == name and l["value"] not in seen:
                keep.append(l); seen.add(l["value"])
    for l in res[:1] + sup[:1]:
        if l["value"] not in seen:
            keep.append(l); seen.add(l["value"])
    return keep or dedup[:4]
