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


# Descanso tras cerrar una operación antes de abrir otra en el MISMO activo (foco)
_REENTRY_COOLDOWN_S = 20


def record(symbol_key: str, direction: str, expiry_seconds: int, entry_price: float,
           source: str = "auto", features=None) -> None:
    """Registra UNA operación accionable (SUBE/BAJA) con CONCENTRACIÓN: una sola
    operación por activo a la vez. Mientras haya una en curso —o recién cerrada— no
    abre otra, para que el sistema se enfoque en operarla y aprender de su resultado.
    `features` = foto de indicadores en la entrada (para que el modelo aprenda)."""
    if direction not in ("SUBE", "BAJA") or not entry_price:
        return
    now = time.time()
    for s in cloud.signals_all():
        if s.get("symbol") != symbol_key:
            continue
        # 1) Ya hay una operación EN CURSO de este activo -> concéntrate en ella
        if s.get("status") == "pending" and now < float(s.get("entry_ts", 0)) + int(
                s.get("expiry_seconds", 0)):
            return
        # 2) Una operación de este activo cerró hace muy poco -> respira antes de reentrar
        if s.get("status") in ("win", "loss") and 0 <= now - (
                float(s.get("entry_ts", 0)) + int(s.get("expiry_seconds", 0))) < _REENTRY_COOLDOWN_S:
            return
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


def _trade_row(s: dict, status: str, ets: float, exp: int) -> dict:
    ex = s.get("exit_price")
    return {
        "direction": s.get("direction"),
        "entry_price": float(s.get("entry_price", 0) or 0),
        "exit_price": float(ex) if ex not in (None, "") else None,
        "entry_ts": ets,
        "expiry_seconds": exp,
        "ends_ts": ets + exp,
        "status": status,          # pending | win | loss
    }


def active_trades(symbol_key: str, include_recent: bool = True,
                  recent_window: int = 1800) -> list:
    """Operaciones del símbolo para MARCARLAS en la gráfica (estilo IQ Option).

    Devuelve las PENDIENTES (línea viva con su cuenta atrás) y, si se pide, las
    últimas ya resueltas (ACIERTO/FALLO dentro de `recent_window` segundos) para
    que veas dónde entró la señal y cómo terminó — así se aprende mirando.
    """
    now = time.time()
    out = []
    for s in cloud.signals_all():
        if s.get("symbol") != symbol_key:
            continue
        status = s.get("status")
        ets = float(s.get("entry_ts", 0) or 0)
        exp = int(s.get("expiry_seconds", 0) or 0)
        if not ets or not float(s.get("entry_price", 0) or 0):
            continue
        if status == "pending":
            out.append(_trade_row(s, "pending", ets, exp))
        elif include_recent and status in ("win", "loss") \
                and now - (ets + exp) <= recent_window:
            out.append(_trade_row(s, status, ets, exp))
    out.sort(key=lambda t: t["entry_ts"])
    return out


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


def ia_stats() -> dict:
    """Mide cuánto ACIERTA el cerebro: compara la precisión de las operaciones donde la
    IA CONFIRMÓ la dirección (marca '+iaok' en source) frente al total. Sirve para saber
    si conviene fiarse más o menos del veredicto del cerebro."""
    agree_n = agree_w = disc_n = disc_w = tot_n = tot_w = 0
    for s in _resolved():
        win = 1 if s["status"] == "win" else 0
        tot_n += 1; tot_w += win
        src = str(s.get("source") or "")
        if "+iaok" in src:
            agree_n += 1; agree_w += win
        elif "+iano" in src:
            disc_n += 1; disc_w += win
    acc = lambda w, n: round(100 * w / n, 1) if n else 0.0
    return {"agree_n": agree_n, "agree_acc": acc(agree_w, agree_n),
            "disc_n": disc_n, "disc_acc": acc(disc_w, disc_n),
            "overall_n": tot_n, "overall_acc": acc(tot_w, tot_n)}


def ia_scale(min_samples: int = 12) -> float:
    """PESO del cerebro (0.4..1.4) según su acierto histórico real. Si con muestra
    suficiente las señales confirmadas por la IA ACIERTAN MÁS que la media, la IA pesa
    más; si aciertan menos, pesa menos. Sin datos suficientes, peso neutro (1.0)."""
    s = ia_stats()
    if s["agree_n"] < min_samples:
        return 1.0
    edge = s["agree_acc"] - s["overall_acc"]      # cuánto mejora la IA sobre la media
    return round(max(0.4, min(1.4, 1.0 + edge / 20.0)), 2)  # +/-1% acc -> +/-0.05 peso


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


def hourly_stats(symbol_key: str | None = None) -> dict:
    """Precisión por HORA del día (UTC) a partir de resultados reales: sirve para que el
    sistema aprenda EN QUÉ HORAS acierta más y evite automáticamente las peores."""
    from collections import defaultdict
    agg = defaultdict(lambda: [0, 0])   # hora -> [aciertos, total]
    for s in _resolved(symbol_key):
        try:
            h = time.gmtime(float(s.get("entry_ts", 0))).tm_hour
        except Exception:
            continue
        agg[h][0] += 1 if s["status"] == "win" else 0
        agg[h][1] += 1
    return {h: {"wins": w, "total": t, "acc": round(100 * w / t, 1) if t else 0.0}
            for h, (w, t) in sorted(agg.items())}


def hour_winrate(hour: int | None = None, symbol_key: str | None = None,
                 min_samples: int = 8) -> float | None:
    """Precisión histórica de una HORA (UTC) si hay muestra suficiente; None si no."""
    h = hour if hour is not None else time.gmtime().tm_hour
    hs = hourly_stats(symbol_key).get(h)
    return hs["acc"] if hs and hs["total"] >= min_samples else None


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
