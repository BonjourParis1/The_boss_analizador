"""
analysis/engine.py — Motor de decisiones.

Combina los indicadores en una recomendación clara (COMPRA / VENTA / MANTENER)
con un nivel de confianza, una explicación en lenguaje sencillo (modo
principiante) y una gestión de riesgo (stop loss / take profit basados en ATR).

Reglas implementadas (ponderadas por votos):
  * RSI < 30  -> sobreventa -> voto COMPRA ;  RSI > 70 -> sobrecompra -> voto VENTA.
  * Cruce de medias móviles (SMA9 vs SMA21) -> cambio de tendencia.
  * MACD cruzando su señal -> momentum.
  * Ruptura de Bandas de Bollinger -> volatilidad/breakout.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

BUY, SELL, HOLD = "COMPRA", "VENTA", "MANTENER"
ICON = {BUY: "📈", SELL: "📉", HOLD: "⏸"}


@dataclass
class Signal:
    symbol_key: str
    action: str                 # COMPRA | VENTA | MANTENER
    confidence: float           # 0..100
    price: float
    reasons: list[str] = field(default_factory=list)         # lectura técnica del experto
    beginner_notes: list[str] = field(default_factory=list)  # comentario del analista
    stop_loss: float | None = None
    take_profit: float | None = None
    rsi: float | None = None
    atr: float | None = None
    adx: float | None = None         # fuerza de tendencia (Wilder): <20 rango, >25 tendencia
    news_score: float | None = None  # sentimiento de noticias (-1..1)
    trend: str | None = None         # alcista | bajista | lateral
    patterns: list[str] = field(default_factory=list)  # patrones de velas detectados
    support: float | None = None
    resistance: float | None = None

    @property
    def icon(self) -> str:
        return ICON.get(self.action, "⏸")

    @property
    def is_strong(self) -> bool:
        """Señal fuerte: dispara alerta visual/sonora en la UI."""
        return self.action in (BUY, SELL) and self.confidence >= 65


def _cross_up(prev_a, prev_b, a, b) -> bool:
    return prev_a <= prev_b and a > b


def _cross_down(prev_a, prev_b, a, b) -> bool:
    return prev_a >= prev_b and a < b


def analyze(symbol_key: str, df_ind: pd.DataFrame,
            news_score: float | None = None, candles=None) -> Signal:
    """Genera la señal a partir del DataFrame con indicadores ya calculados.

    `news_score` (sentimiento de noticias en -1..1) y `candles` (lectura de velas
    de analysis.patterns) son factores que refuerzan o suavizan la señal técnica,
    nunca la sustituyen.
    """
    if len(df_ind) < 2:
        last = df_ind.iloc[-1]
        return Signal(symbol_key, HOLD, 0.0, float(last["close"]),
                      ["Datos insuficientes."], ["Esperando más datos del mercado."],
                      news_score=news_score)

    last = df_ind.iloc[-1]
    prev = df_ind.iloc[-2]
    price = float(last["close"])

    buy_votes = 0.0
    sell_votes = 0.0
    reasons: list[str] = []
    notes: list[str] = []

    # --- 1) RSI ---
    rsi_val = float(last["rsi"])
    if rsi_val < 30:
        buy_votes += 1.5
        reasons.append(f"RSI={rsi_val:.1f} (<30, sobreventa).")
        notes.append("El RSI está bajo, lo que indica sobreventa. Suele ser una "
                     "oportunidad de COMPRA.")
    elif rsi_val > 70:
        sell_votes += 1.5
        reasons.append(f"RSI={rsi_val:.1f} (>70, sobrecompra).")
        notes.append("El RSI está alto, lo que indica sobrecompra. Suele anticipar "
                     "una caída: posible VENTA.")
    else:
        notes.append(f"El RSI ({rsi_val:.0f}) está en zona neutral (entre 30 y 70).")

    # --- 2) Cruce de medias móviles SMA9 / SMA21 ---
    if _cross_up(prev["sma_fast"], prev["sma_slow"], last["sma_fast"], last["sma_slow"]):
        buy_votes += 1.0
        reasons.append("Cruce alcista de medias (SMA9 cruza por encima de SMA21).")
        notes.append("La media rápida cruzó hacia arriba la lenta: cambio de "
                     "tendencia a ALCISTA.")
    elif _cross_down(prev["sma_fast"], prev["sma_slow"], last["sma_fast"], last["sma_slow"]):
        sell_votes += 1.0
        reasons.append("Cruce bajista de medias (SMA9 cruza por debajo de SMA21).")
        notes.append("La media rápida cruzó hacia abajo la lenta: cambio de "
                     "tendencia a BAJISTA.")

    # --- 3) MACD cruzando su línea de señal ---
    if _cross_up(prev["macd"], prev["macd_signal"], last["macd"], last["macd_signal"]):
        buy_votes += 0.8
        reasons.append("MACD cruza al alza su señal (momentum positivo).")
    elif _cross_down(prev["macd"], prev["macd_signal"], last["macd"], last["macd_signal"]):
        sell_votes += 0.8
        reasons.append("MACD cruza a la baja su señal (momentum negativo).")

    # --- 4) Ruptura de Bandas de Bollinger ---
    if price < last["bb_lower"]:
        buy_votes += 0.7
        reasons.append("Precio por debajo de la banda inferior de Bollinger.")
        notes.append("El precio rompió la banda inferior: posible rebote al alza.")
    elif price > last["bb_upper"]:
        sell_votes += 0.7
        reasons.append("Precio por encima de la banda superior de Bollinger.")
        notes.append("El precio rompió la banda superior: posible corrección a la baja.")

    # --- 5) Lectura de velas: patrones y tendencia ---
    trend = patterns_names = None
    support = resistance = None
    if candles is not None:
        trend = candles.trend
        patterns_names = [p.name for p in candles.patterns]
        support, resistance = candles.support, candles.resistance
        # Patrones de velas
        if candles.bull_score > candles.bear_score:
            buy_votes += 0.9
            reasons.append("Velas con patrón alcista: " +
                           ", ".join(p.name for p in candles.patterns if p.bias == "alcista") + ".")
        elif candles.bear_score > candles.bull_score:
            sell_votes += 0.9
            reasons.append("Velas con patrón bajista: " +
                           ", ".join(p.name for p in candles.patterns if p.bias == "bajista") + ".")
        # Tendencia (acompaña, con peso por su fuerza)
        if trend == "alcista":
            buy_votes += 0.7 * (0.5 + candles.trend_strength)
            reasons.append(f"Tendencia alcista (fuerza {candles.trend_strength:.0%}).")
        elif trend == "bajista":
            sell_votes += 0.7 * (0.5 + candles.trend_strength)
            reasons.append(f"Tendencia bajista (fuerza {candles.trend_strength:.0%}).")

    # --- 6) Sentimiento de noticias (factor secundario) ---
    if news_score is not None:
        if news_score > 0.08:
            buy_votes += 0.6
            reasons.append(f"Noticias con sentimiento positivo ({news_score:+.2f}).")
            notes.append("El flujo de noticias recientes es favorable; acompaña a la compra.")
        elif news_score < -0.08:
            sell_votes += 0.6
            reasons.append(f"Noticias con sentimiento negativo ({news_score:+.2f}).")
            notes.append("El flujo de noticias recientes es adverso; prudencia con las compras.")

    # --- Decisión final ---
    total = buy_votes + sell_votes
    if total == 0:
        action = HOLD
        confidence = 25.0
        notes.append("No hay señales claras. Lo prudente es MANTENER y esperar.")
    elif buy_votes > sell_votes:
        action = BUY
        confidence = min(95.0, 40 + (buy_votes - sell_votes) * 18)
    elif sell_votes > buy_votes:
        action = SELL
        confidence = min(95.0, 40 + (sell_votes - buy_votes) * 18)
    else:
        action = HOLD
        confidence = 30.0
        notes.append("Señales de compra y venta empatadas: MANTENER.")

    # --- Gestión de riesgo basada en ATR ---
    atr_val = float(last["atr"]) if pd.notna(last["atr"]) else 0.0
    stop_loss = take_profit = None
    if action == BUY and atr_val > 0:
        stop_loss = round(price - 1.5 * atr_val, 6)
        take_profit = round(price + 2.0 * atr_val, 6)  # ratio riesgo/beneficio ~1:1.3
    elif action == SELL and atr_val > 0:
        stop_loss = round(price + 1.5 * atr_val, 6)
        take_profit = round(price - 2.0 * atr_val, 6)

    return Signal(
        symbol_key=symbol_key,
        action=action,
        confidence=round(confidence, 1),
        price=price,
        reasons=reasons or ["Sin disparadores técnicos relevantes."],
        beginner_notes=notes,
        stop_loss=stop_loss,
        take_profit=take_profit,
        rsi=round(rsi_val, 1),
        atr=round(atr_val, 6),
        adx=round(float(last["adx"]), 1) if "adx" in df_ind and pd.notna(last["adx"]) else None,
        news_score=news_score,
        trend=trend,
        patterns=patterns_names or [],
        support=round(support, 6) if support else None,
        resistance=round(resistance, 6) if resistance else None,
    )
