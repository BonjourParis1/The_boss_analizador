"""
analysis/sessions.py — Filtro de SESIÓN/HORARIO (liquidez).

Operar en horas de baja liquidez (sesión asiática muerta en forex, fuera del horario
de Wall Street en acciones, madrugada en cripto) da spreads amplios, movimientos
erráticos y falsas señales. Este módulo clasifica la calidad de liquidez del momento
para cada tipo de activo y permite EVITAR operar cuando es baja.

Horarios en UTC. Ventanas algo generosas para cubrir horario de verano/invierno.
"""
from __future__ import annotations

from datetime import datetime


def _note(q: str, mkt: str) -> str:
    return {"alta": f"Liquidez alta ({mkt})",
            "media": f"Liquidez media ({mkt})",
            "baja": f"Baja liquidez ({mkt}): mejor esperar"}.get(q, mkt)


def session_state(symbol, now: datetime | None = None) -> dict:
    """Estado de sesión del activo: {open, quality (alta/media/baja/cerrado), note}."""
    now = now or datetime.utcnow()
    wd = now.weekday()                    # 0=lun … 6=dom
    h = now.hour + now.minute / 60.0
    typ = getattr(symbol, "type", "cripto")

    if typ == "cripto":                   # 24/7, pero con altibajos de liquidez
        weekend = wd >= 5
        dead = h < 6                      # madrugada UTC: menor actividad
        q = "baja" if (weekend and dead) else "media" if (weekend or dead) else "alta"
        return {"open": True, "quality": q, "note": _note(q, "cripto 24/7")}

    if typ == "forex":                    # cerrado el fin de semana
        if wd == 5 or (wd == 4 and h >= 21) or (wd == 6 and h < 21):
            return {"open": False, "quality": "cerrado",
                    "note": "Forex cerrado (fin de semana)"}
        overlap = 12 <= h < 16           # solape Londres–Nueva York: máxima liquidez
        active = 7 <= h < 21             # Londres o Nueva York
        q = "alta" if overlap else "media" if active else "baja"   # baja = asiática/rollover
        return {"open": True, "quality": q, "note": _note(q, "forex")}

    # Acciones / índices / materias (referencia: sesión de EE. UU.)
    if wd >= 5:
        return {"open": False, "quality": "cerrado",
                "note": "Mercado cerrado (fin de semana)"}
    rth = 13.5 <= h < 21                  # ~9:30–16:00 ET con margen verano/invierno
    if not rth:
        return {"open": False, "quality": "baja",
                "note": "Fuera del horario principal de EE. UU. (baja liquidez)"}
    power = (13.5 <= h < 15) or (19.5 <= h < 21)   # primera y última hora
    q = "alta" if power else "media"
    return {"open": True, "quality": q, "note": _note(q, "acciones/índices")}


def tradeable(symbol, high_precision: bool = False, now: datetime | None = None):
    """(ok, motivo). ok=False si NO conviene operar por liquidez/horario.

    Bloquea siempre la baja liquidez y el mercado cerrado; en modo alta precisión,
    exige además liquidez ALTA (bloquea también la 'media')."""
    s = session_state(symbol, now)
    if not s["open"] or s["quality"] in ("baja", "cerrado"):
        return False, s["note"]
    if high_precision and s["quality"] == "media":
        return False, "Alta precisión: se opera solo en liquidez alta · " + s["note"]
    return True, s["note"]
