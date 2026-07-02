"""
analysis/regime.py — CONTEXTO DE LARGO PLAZO (años) del mercado.

El motor de corto plazo (velas de minutos) es reactivo. Para que la guía sea fiable
como un analista profesional, cada recomendación se contrasta con el "régimen" de
fondo derivado de AÑOS de historia (velas semanales/mensuales):

  * Tendencia mayor  -> precio vs. su media larga (30 semanas ≈ 200 días) y pendiente.
  * Posición en el rango histórico (máx/mín de ~5 años): ¿caro o barato de fondo?
  * Momentum anual    -> rendimiento de los últimos ~12 meses.

Con eso se clasifica el régimen (ALCISTA / BAJISTA / LATERAL) y su fuerza (0..1).
Ese contexto SESGA las señales de corto plazo: operar A FAVOR del régimen es más
fiable; operar EN CONTRA de un régimen fuerte se penaliza o se pospone (ESPERAR).

Honestidad: es contexto probabilístico de fondo, no una garantía. Combina lo de años
con la actualidad (las velas más recientes ya están incluidas en la serie).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class Regime:
    direction: str                 # ALCISTA | BAJISTA | LATERAL
    strength: float                # 0..1 (qué tan marcado es el régimen)
    price: float = 0.0
    ma_long: float | None = None   # media larga (30 semanas)
    range_pct: float | None = None # 0..100: posición en el rango de ~5 años
    annual_return: float | None = None  # rendimiento ~12 meses (fracción)
    years: float = 0.0             # cuántos años de historia se analizaron
    notes: list[str] = field(default_factory=list)

    @property
    def bias(self) -> str:
        """Traducción a la nomenclatura del asesor (SUBE/BAJA/ESPERAR)."""
        return {"ALCISTA": "SUBE", "BAJISTA": "BAJA"}.get(self.direction, "ESPERAR")

    @property
    def is_strong(self) -> bool:
        return self.strength >= 0.55 and self.direction in ("ALCISTA", "BAJISTA")


def _slope(series: pd.Series, n: int = 12) -> float:
    """Pendiente normalizada de los últimos n puntos (−1..1 aprox)."""
    s = series.dropna()
    if len(s) < n:
        return 0.0
    y = s.iloc[-n:].to_numpy(dtype=float)
    x = range(len(y))
    import numpy as np
    m = np.polyfit(x, y, 1)[0]
    avg = float(y.mean()) or 1.0
    return float(m * len(y) / avg)   # cambio relativo sobre la ventana


def compute(df_weekly: pd.DataFrame, periods_per_year: int = 52) -> Regime:
    """Deriva el régimen de fondo desde una serie LARGA (velas semanales, ~años).

    `df_weekly` debe traer al menos la columna 'close' con índice temporal creciente.
    """
    if df_weekly is None or "close" not in df_weekly or len(df_weekly) < 8:
        return Regime("LATERAL", 0.0, notes=["Sin suficiente historia de largo plazo."])

    close = df_weekly["close"].astype(float)
    price = float(close.iloc[-1])
    n = len(close)
    years = round(n / periods_per_year, 1)

    # 1) Media larga (30 periodos ≈ 200 días si son semanas) y posición del precio
    win = min(30, max(8, n // 2))
    ma_long = float(close.rolling(win).mean().iloc[-1])
    above = price > ma_long
    ma_gap = (price - ma_long) / ma_long if ma_long else 0.0

    # 2) Posición dentro del rango histórico completo (caro/barato de fondo)
    hi, lo = float(close.max()), float(close.min())
    range_pct = 100 * (price - lo) / (hi - lo) if hi > lo else 50.0

    # 3) Momentum anual (precio vs ~1 año atrás)
    look = min(periods_per_year, n - 1)
    annual_return = (price / float(close.iloc[-1 - look]) - 1.0) if look > 0 else 0.0

    # 4) Pendiente reciente de la media larga (confirma dirección de fondo)
    slope = _slope(close.rolling(win).mean(), n=min(12, n))

    # --- Puntuación de dirección: votos alcistas menos bajistas, ponderados ---
    score = 0.0
    if above:
        score += 1.0 + min(abs(ma_gap) * 5, 1.0)
    else:
        score -= 1.0 + min(abs(ma_gap) * 5, 1.0)
    if annual_return > 0.05:
        score += 1.0
    elif annual_return < -0.05:
        score -= 1.0
    if slope > 0.02:
        score += 0.8
    elif slope < -0.02:
        score -= 0.8

    strength = min(1.0, abs(score) / 3.2)
    if score >= 1.0:
        direction = "ALCISTA"
    elif score <= -1.0:
        direction = "BAJISTA"
    else:
        direction = "LATERAL"
        strength = min(strength, 0.4)

    notes = [
        f"Tendencia de fondo {direction} (fuerza {strength:.0%}) según ~{years} años.",
        f"Precio {'sobre' if above else 'bajo'} su media larga ({ma_gap:+.1%}).",
        f"Rendimiento ~12 meses: {annual_return:+.1%}.",
        f"Posición en el rango histórico: {range_pct:.0f}% "
        f"({'zona alta' if range_pct > 70 else 'zona baja' if range_pct < 30 else 'zona media'}).",
    ]
    return Regime(direction, round(strength, 2), price, round(ma_long, 6),
                  round(range_pct, 1), round(annual_return, 4), years, notes)


def apply_to_plan(plan, regime: Regime):
    """Ajusta un TradePlan de corto plazo con el contexto de LARGO plazo.

    * A favor del régimen fuerte  -> más confianza (operación más fiable).
    * En contra de un régimen fuerte -> penaliza; si es muy fuerte, ESPERAR
      (no se opera contra la tendencia de años salvo evidencia enorme).
    * Régimen lateral -> ligera cautela (menos fiable operar de fondo).
    """
    if regime is None or plan.direction not in ("SUBE", "BAJA"):
        return plan
    reasons = list(plan.rationale)
    if regime.is_strong:
        if plan.direction == regime.bias:
            plan.confidence = round(min(98.0, plan.confidence + 6 + 6 * regime.strength), 1)
            reasons.append(f"✅ A favor de la tendencia de fondo {regime.direction} "
                           f"(~{regime.years} años): más fiable.")
        else:
            if regime.strength >= 0.75:
                reasons.append(f"⛔ En CONTRA de una tendencia de fondo {regime.direction} "
                               f"muy marcada (~{regime.years} años): lo prudente es ESPERAR.")
                plan.direction = "ESPERAR"
                plan.action_label, plan.icon = "ESPERAR", "⏸"
                plan.duration_label, plan.expiry_seconds = "—", 0
                plan.confidence = round(min(plan.confidence, 45.0), 1)
            else:
                plan.confidence = round(max(0.0, plan.confidence - 12 - 10 * regime.strength), 1)
                reasons.append(f"⚠️ Contra la tendencia de fondo {regime.direction}: menos fiable.")
    elif regime.direction == "LATERAL":
        plan.confidence = round(max(0.0, plan.confidence - 5), 1)
        reasons.append("Mercado sin tendencia de fondo clara (lateral en años): cautela.")
    plan.rationale = reasons
    return plan
