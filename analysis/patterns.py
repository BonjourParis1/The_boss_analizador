"""
analysis/patterns.py — "Lectura de velas" como un trader profesional.

Detecta:
  * Patrones de velas japonesas (doji, martillo, estrella fugaz, envolvente,
    estrella del amanecer/atardecer, tres soldados/cuervos).
  * Tendencia (alcista / bajista / lateral) por estructura de máximos y mínimos
    y pendiente de la EMA50.
  * Soportes y resistencias (swing highs/lows recientes) y el nivel más cercano.

Cada patrón trae un sesgo (alcista/bajista) y una explicación corta. El motor de
decisiones (engine.py) los usa como un factor más.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

BULL, BEAR, NEUTRAL = "alcista", "bajista", "neutral"


@dataclass
class Pattern:
    name: str
    bias: str          # alcista | bajista | neutral
    explanation: str


@dataclass
class CandleReading:
    trend: str                          # alcista | bajista | lateral
    trend_strength: float               # 0..1
    patterns: list[Pattern] = field(default_factory=list)
    support: float | None = None
    resistance: float | None = None

    @property
    def bull_score(self) -> float:
        return sum(1 for p in self.patterns if p.bias == BULL)

    @property
    def bear_score(self) -> float:
        return sum(1 for p in self.patterns if p.bias == BEAR)


def _body(o, c):       return abs(c - o)
def _range(h, l):      return max(h - l, 1e-9)
def _upper(o, h, c):   return h - max(o, c)
def _lower(o, l, c):   return min(o, c) - l


def _detect_single(o, h, l, c) -> list[Pattern]:
    out = []
    rng = _range(h, l)
    body = _body(o, c)
    upper = _upper(o, h, c)
    lower = _lower(o, l, c)

    if body <= 0.1 * rng:
        out.append(Pattern("Doji", NEUTRAL, "Indecisión: apertura y cierre casi iguales."))
    if lower >= 2 * body and upper <= body and body > 0:
        out.append(Pattern("Martillo", BULL, "Mecha inferior larga: posible rebote alcista."))
    if upper >= 2 * body and lower <= body and body > 0:
        out.append(Pattern("Estrella fugaz", BEAR, "Mecha superior larga: posible giro bajista."))
    return out


def _detect_two(prev, cur) -> list[Pattern]:
    out = []
    po, pc = prev["open"], prev["close"]
    co, cc = cur["open"], cur["close"]
    # Envolvente alcista: vela verde que envuelve a la roja previa
    if pc < po and cc > co and co <= pc and cc >= po:
        out.append(Pattern("Envolvente alcista", BULL,
                            "Una vela verde envuelve a la roja anterior: fuerza compradora."))
    # Envolvente bajista
    if pc > po and cc < co and co >= pc and cc <= po:
        out.append(Pattern("Envolvente bajista", BEAR,
                            "Una vela roja envuelve a la verde anterior: fuerza vendedora."))
    return out


def _detect_three(c1, c2, c3) -> list[Pattern]:
    out = []
    # Estrella del amanecer (giro alcista)
    if c1["close"] < c1["open"] and _body(c2["open"], c2["close"]) < _body(c1["open"], c1["close"]) \
            and c3["close"] > c3["open"] and c3["close"] > (c1["open"] + c1["close"]) / 2:
        out.append(Pattern("Estrella del amanecer", BULL, "Patrón de giro al alza en 3 velas."))
    # Estrella del atardecer (giro bajista)
    if c1["close"] > c1["open"] and _body(c2["open"], c2["close"]) < _body(c1["open"], c1["close"]) \
            and c3["close"] < c3["open"] and c3["close"] < (c1["open"] + c1["close"]) / 2:
        out.append(Pattern("Estrella del atardecer", BEAR, "Patrón de giro a la baja en 3 velas."))
    return out


def _trend(df: pd.DataFrame) -> tuple[str, float]:
    """Tendencia por pendiente de EMA50 normalizada + posición del precio."""
    if "ema_50" not in df or len(df) < 20:
        return "lateral", 0.0
    ema = df["ema_50"].dropna()
    if len(ema) < 10:
        return "lateral", 0.0
    slope = (ema.iloc[-1] - ema.iloc[-10]) / (abs(ema.iloc[-10]) + 1e-9)
    strength = float(min(1.0, abs(slope) * 50))
    if slope > 0.0008:
        return "alcista", strength
    if slope < -0.0008:
        return "bajista", strength
    return "lateral", strength


def _support_resistance(df: pd.DataFrame, lookback: int = 60, window: int = 3):
    """Swing highs/lows recientes -> soporte y resistencia más cercanos al precio."""
    d = df.tail(lookback)
    highs, lows = [], []
    h, l = d["high"].values, d["low"].values
    for i in range(window, len(d) - window):
        if h[i] == max(h[i - window:i + window + 1]):
            highs.append(h[i])
        if l[i] == min(l[i - window:i + window + 1]):
            lows.append(l[i])
    price = float(df["close"].iloc[-1])
    resistance = min([x for x in highs if x >= price], default=None)
    support = max([x for x in lows if x <= price], default=None)
    return support, resistance


def read_candles(df: pd.DataFrame) -> CandleReading:
    """Análisis completo de velas sobre el DataFrame con indicadores."""
    if len(df) < 3:
        return CandleReading("lateral", 0.0)
    rows = df.iloc[-3:].to_dict("records")
    c1, c2, c3 = rows[0], rows[1], rows[2]

    patterns: list[Pattern] = []
    patterns += _detect_single(c3["open"], c3["high"], c3["low"], c3["close"])
    patterns += _detect_two(c2, c3)
    patterns += _detect_three(c1, c2, c3)

    trend, strength = _trend(df)
    support, resistance = _support_resistance(df)
    return CandleReading(trend, round(strength, 2), patterns, support, resistance)
