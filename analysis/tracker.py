"""
analysis/tracker.py — Registro de resultados y autoaprendizaje por aciertos/fallos.

Cada señal accionable (COMPRA/VENTA con su duración) se registra con el precio de
entrada. Al vencer la duración, el sistema compara con el precio REAL y la marca como
ACIERTO o FALLO automáticamente — así "sabe cuándo falló". La precisión resultante se
muestra y retroalimenta la confianza del motor (aprende con el tiempo).

Persistencia: SUPABASE (db/cloud.py). Si Supabase no está configurado, cae a un
archivo local solo como respaldo. La lógica vive aquí; el almacenamiento, en la nube.
"""
from __future__ import annotations

import time

from db import cloud

_DUR_LABEL = {30: "30s", 60: "1m", 180: "3m", 300: "5m", 900: "15m"}


def record(symbol_key: str, direction: str, expiry_seconds: int, entry_price: float,
           source: str = "auto", features=None) -> None:
    """Registra una señal accionable (SUBE/BAJA). Evita duplicar la misma pendiente.
    `features` = foto de indicadores en la entrada (para que el modelo aprenda)."""
    if direction not in ("SUBE", "BAJA") or not entry_price:
        return
    now = time.time()
    for s in cloud.signals_all():
        if (s.get("symbol") == symbol_key and s.get("status") == "pending"
                and s.get("direction") == direction
                and now - float(s.get("entry_ts", 0)) < max(expiry_seconds, 30)):
            return  # ya hay una pendiente igual reciente
    cloud.signal_save(symbol_key, direction, expiry_seconds, entry_price, source, features)


def evaluate(symbol_key: str, current_price: float) -> None:
    """Marca acierto/fallo de las señales del símbolo cuya duración ya venció."""
    if not current_price:
        return
    now = time.time()
    for s in cloud.signals_all():
        if (s.get("symbol") == symbol_key and s.get("status") == "pending"
                and now >= float(s.get("entry_ts", 0)) + int(s.get("expiry_seconds", 0))):
            up = current_price > float(s.get("entry_price", 0))
            win = (s["direction"] == "SUBE" and up) or (s["direction"] == "BAJA" and not up)
            cloud.signal_update(s.get("id"), "win" if win else "loss", current_price)


def mark_last(symbol_key: str, win: bool) -> bool:
    """Marca manualmente el resultado de la última señal del símbolo (tu resultado real)."""
    rows = [s for s in cloud.signals_all()
            if s.get("symbol") == symbol_key]
    rows.sort(key=lambda s: float(s.get("entry_ts", 0)), reverse=True)
    if rows:
        cloud.signal_update(rows[0].get("id"), "win" if win else "loss",
                            rows[0].get("entry_price", 0))
        return True
    return False


def _resolved(symbol_key: str | None = None) -> list:
    return [s for s in cloud.signals_all()
            if s.get("status") in ("win", "loss")
            and (symbol_key is None or s.get("symbol") == symbol_key)]


def stats(symbol_key: str | None = None) -> dict:
    """Precisión global o por símbolo: aciertos/fallos y % de acierto."""
    rel = _resolved(symbol_key)
    n = len(rel)
    wins = sum(1 for s in rel if s["status"] == "win")
    return {"n": n, "wins": wins, "losses": n - wins,
            "accuracy": round(100 * wins / n, 1) if n else 0.0}


def live_winrate(symbol_key: str, min_samples: int = 8) -> float | None:
    """Precisión por símbolo si hay muestras suficientes (para ajustar confianza)."""
    s = stats(symbol_key)
    return s["accuracy"] if s["n"] >= min_samples else None


def evaluated() -> list:
    """Señales ya resueltas (acierto/fallo), ordenadas por tiempo."""
    return sorted(_resolved(), key=lambda s: float(s.get("entry_ts", 0)))


def curve() -> list:
    """Curva de precisión acumulada (win-rate) a lo largo de las señales."""
    out, w = [], 0
    for i, s in enumerate(evaluated(), 1):
        if s["status"] == "win":
            w += 1
        out.append({"señal": i, "precisión": round(100 * w / i, 1)})
    return out


def _breakdown(keyfn) -> dict:
    from collections import defaultdict
    agg = defaultdict(lambda: [0, 0])
    for s in evaluated():
        k = keyfn(s)
        agg[k][0] += 1 if s["status"] == "win" else 0
        agg[k][1] += 1
    return {k: {"aciertos": v[0], "total": v[1],
                "precisión": round(100 * v[0] / v[1], 1)} for k, v in agg.items()}


def breakdown_symbol() -> dict:
    return _breakdown(lambda s: s.get("symbol"))


def breakdown_duration() -> dict:
    return _breakdown(
        lambda s: _DUR_LABEL.get(int(s.get("expiry_seconds", 0)),
                                 str(s.get("expiry_seconds", "?")) + "s"))


def reset() -> None:
    """Borra el historial local de respaldo (en Supabase se gestiona desde la consola)."""
    cloud._lsave(cloud._SFILE, [])
    cloud._cache["ts"] = 0.0
    cloud._cache["signals"] = None
