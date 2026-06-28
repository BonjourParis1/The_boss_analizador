"""
analysis/tracker.py — Registro de resultados y autoaprendizaje por aciertos/fallos.

Cada señal accionable (COMPRA/VENTA con su duración) se registra con el precio de
entrada. Al vencer la duración, el sistema compara con el precio REAL y la marca como
ACIERTO o FALLO automáticamente — así "sabe cuándo falló". La precisión resultante se
muestra y retroalimenta la confianza del motor (aprende con el tiempo).

Persistencia local en .secrets/signal_log.json (ignorado por git).
"""
from __future__ import annotations

import json
import threading
import time

from config import SECRETS_DIR

_FILE = SECRETS_DIR / "signal_log.json"
_lock = threading.Lock()
_MAX = 1000


def _load() -> list:
    if _FILE.exists():
        try:
            return json.loads(_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save(data: list) -> None:
    try:
        _FILE.write_text(json.dumps(data[-_MAX:]), encoding="utf-8")
    except Exception:
        pass


def record(symbol_key: str, direction: str, expiry_seconds: int, entry_price: float,
           source: str = "auto") -> None:
    """Registra una señal accionable (SUBE/BAJA). Evita duplicar la misma pendiente."""
    if direction not in ("SUBE", "BAJA") or not entry_price:
        return
    now = time.time()
    with _lock:
        data = _load()
        for s in data:
            if (s["symbol"] == symbol_key and s["status"] == "pending"
                    and s["dir"] == direction and now - s["ts"] < max(expiry_seconds, 30)):
                return  # ya hay una pendiente igual reciente
        data.append({"symbol": symbol_key, "dir": direction, "exp": int(expiry_seconds),
                     "entry": float(entry_price), "ts": now, "status": "pending",
                     "src": source})
        _save(data)


def evaluate(symbol_key: str, current_price: float) -> None:
    """Marca acierto/fallo de las señales del símbolo cuya duración ya venció."""
    if not current_price:
        return
    now = time.time()
    changed = False
    with _lock:
        data = _load()
        for s in data:
            if s["symbol"] == symbol_key and s["status"] == "pending" \
                    and now >= s["ts"] + s["exp"]:
                up = current_price > s["entry"]
                win = (s["dir"] == "SUBE" and up) or (s["dir"] == "BAJA" and not up)
                s["status"] = "win" if win else "loss"
                s["exit"] = float(current_price)
                changed = True
        if changed:
            _save(data)


def mark_last(symbol_key: str, win: bool) -> bool:
    """Marca manualmente el resultado de la última señal del símbolo (tu resultado real)."""
    with _lock:
        data = _load()
        for s in reversed(data):
            if s["symbol"] == symbol_key:
                s["status"] = "win" if win else "loss"
                s["src"] = "manual"
                _save(data)
                return True
    return False


def stats(symbol_key: str | None = None) -> dict:
    """Precisión global o por símbolo: aciertos/fallos y % de acierto."""
    data = _load()
    rel = [s for s in data if s["status"] in ("win", "loss")
           and (symbol_key is None or s["symbol"] == symbol_key)]
    n = len(rel)
    wins = sum(1 for s in rel if s["status"] == "win")
    return {"n": n, "wins": wins, "losses": n - wins,
            "accuracy": round(100 * wins / n, 1) if n else 0.0}


def live_winrate(symbol_key: str, min_samples: int = 8) -> float | None:
    """Precisión por símbolo si hay muestras suficientes (para ajustar confianza)."""
    s = stats(symbol_key)
    return s["accuracy"] if s["n"] >= min_samples else None


_DUR_LABEL = {30: "30s", 60: "1m", 180: "3m", 300: "5m", 900: "15m"}


def evaluated() -> list:
    """Señales ya resueltas (acierto/fallo), ordenadas por tiempo."""
    return sorted([s for s in _load() if s["status"] in ("win", "loss")],
                  key=lambda s: s["ts"])


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
    return _breakdown(lambda s: s["symbol"])


def breakdown_duration() -> dict:
    return _breakdown(lambda s: _DUR_LABEL.get(s.get("exp"), str(s.get("exp", "?")) + "s"))


def reset() -> None:
    _save([])
