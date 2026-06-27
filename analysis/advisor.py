"""
analysis/advisor.py — Asesor autónomo de operaciones con DURACIÓN sugerida.

Convierte la señal técnica + lectura de velas + (opcional) el autoaprendizaje del
histórico en un "plan de operación" estilo opciones binarias / IQ Option:

    COMPRA (CALL) / VENTA (PUT) / ESPERAR  +  duración sugerida (30s, 1m, 3m, 5m)

La duración se estima por la volatilidad (ATR%) y la fuerza de la señal: mercados
rápidos -> expiraciones cortas; tendencias fuertes y estables -> más largas.

Honestidad: es una SUGERENCIA probabilística para apoyar tu decisión manual, no una
garantía. Cuando la señal es débil o las fuentes se contradicen, recomienda ESPERAR.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from analysis.engine import BUY, HOLD, SELL

# Mapa dirección -> presentación binaria
_DIR = {
    "SUBE": ("COMPRA (CALL)", "📈", "alcista"),
    "BAJA": ("VENTA (PUT)", "📉", "bajista"),
    "ESPERAR": ("ESPERAR", "⏸", "neutral"),
}


@dataclass
class TradePlan:
    direction: str            # SUBE | BAJA | ESPERAR
    action_label: str         # "COMPRA (CALL)" / "VENTA (PUT)" / "ESPERAR"
    icon: str
    duration_label: str       # "30s" | "1m" | "3m" | "5m"
    expiry_seconds: int
    confidence: float         # 0..100
    rationale: list[str] = field(default_factory=list)

    @property
    def is_actionable(self) -> bool:
        return self.direction in ("SUBE", "BAJA") and self.confidence >= 60


def _duration(vol: float, strong: bool) -> tuple[str, int]:
    """Expiración sugerida según volatilidad (ATR%) y fuerza de la señal."""
    if vol >= 0.006:
        return ("30s", 30) if strong else ("1m", 60)
    if vol >= 0.0025:
        return ("1m", 60) if strong else ("3m", 180)
    return ("3m", 180) if strong else ("5m", 300)


def build_plan(sig, auto_pred: str | None = None, auto_conf: float | None = None) -> TradePlan:
    """Genera el plan a partir de la señal del motor y (opcional) el autoaprendizaje.

    `auto_pred` es la etiqueta de analysis.auto_learn.predict (SUBE/LATERAL/BAJA).
    """
    reasons: list[str] = []

    # Dirección base desde el motor técnico
    if sig.action == BUY:
        direction = "SUBE"
    elif sig.action == SELL:
        direction = "BAJA"
    else:
        direction = "ESPERAR"
    conf = float(sig.confidence)
    reasons.append(f"Motor técnico: {sig.action} ({sig.confidence:.0f}%).")

    # Refuerzo / contradicción con el autoaprendizaje del histórico
    if auto_pred:
        if auto_pred in ("SUBE", "BAJA"):
            if direction == "ESPERAR":
                direction = auto_pred                      # el ML propone dirección
                conf = max(conf, (auto_conf or 50) * 0.8)
                reasons.append(f"Autoaprendizaje anticipa {auto_pred} ({auto_conf:.0f}%).")
            elif auto_pred == direction:
                conf = min(98, conf + 12)                  # ambos coinciden -> sube confianza
                reasons.append(f"Autoaprendizaje CONFIRMA {direction} ({auto_conf:.0f}%).")
            else:
                conf = max(0, conf - 20)                   # se contradicen -> baja confianza
                reasons.append(f"⚠️ Autoaprendizaje sugiere lo contrario ({auto_pred}). Cautela.")
        elif auto_pred == "LATERAL":
            conf = max(0, conf - 8)
            reasons.append("Autoaprendizaje ve mercado LATERAL: menos fiable operar.")

    # Tendencia y patrones (de la lectura de velas, ya en sig)
    if sig.trend and sig.trend != "lateral":
        reasons.append(f"Tendencia {sig.trend}.")
    if sig.patterns:
        reasons.append("Patrones: " + ", ".join(sig.patterns) + ".")

    # Si la confianza queda baja, mejor esperar
    if conf < 55:
        direction = "ESPERAR"
        reasons.append("Confianza insuficiente: lo prudente es no operar ahora.")

    # Duración por volatilidad
    price = sig.price or 1.0
    vol = (sig.atr or 0.0) / price if price else 0.0
    strong = conf >= 72
    dur_label, dur_sec = _duration(vol, strong)
    if direction == "ESPERAR":
        dur_label, dur_sec = "—", 0

    action_label, icon, _ = _DIR[direction]
    return TradePlan(direction, action_label, icon, dur_label, dur_sec,
                     round(conf, 1), reasons)
