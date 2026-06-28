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


# Catálogo de duraciones de inversión: (etiqueta, segundos, intervalo de análisis)
DURATIONS = [
    ("30s", 30, "1m"), ("1m", 60, "1m"), ("3m", 180, "3m"),
    ("5m", 300, "5m"), ("15m", 900, "15m"),
]
DURATION_BY_LABEL = {d[0]: d for d in DURATIONS}

# Temporalidades de CONFIRMACIÓN por duración (etiqueta, peso). Las más largas
# pesan más para captar la tendencia de horas/días/meses y dar estabilidad:
# así una operación de 5m no cambia cada 2 min, porque la confirma el 1h/4h/1d.
CONFIRM_TFS = {
    "30s": [("1m", 1.0), ("15m", 1.6), ("1h", 2.0), ("1d", 1.8)],
    "1m":  [("1m", 1.0), ("15m", 1.6), ("1h", 2.0), ("1d", 1.8)],
    "3m":  [("5m", 1.0), ("15m", 1.4), ("1h", 1.8), ("1d", 2.0)],
    "5m":  [("5m", 1.0), ("15m", 1.4), ("1h", 1.8), ("1d", 2.0)],
    "15m": [("15m", 1.0), ("1h", 1.6), ("4h", 2.0), ("1d", 2.2)],
}


def consensus_plan(per_tf, force_duration, auto_pred=None, auto_conf=None,
                   winrate: float | None = None) -> TradePlan:
    """Decide combinando VARIAS temporalidades (multi-timeframe) para más fiabilidad.

    per_tf: lista de (etiqueta_tf, peso, señal). El consenso ponderado evita que el
    plan cambie con cada fluctuación: solo opera cuando las temporalidades (incluida
    la diaria) están alineadas.  winrate = % de acierto del backtest (contexto).
    """
    label, secs = force_duration
    buy_w = sell_w = total = 0.0
    reads = []
    for tf, w, sg in per_tf:
        total += w
        if sg.action == BUY:
            buy_w += w; d = "📈"
        elif sg.action == SELL:
            sell_w += w; d = "📉"
        else:
            d = "⏸"
        reads.append(f"{tf}:{d}")
    reasons = ["Multi-temporalidad → " + "  ".join(reads) + "."]

    if total == 0:
        return TradePlan("ESPERAR", "ESPERAR", "⏸", "—", 0, 30.0, reasons)

    align = max(buy_w, sell_w) / total
    if align >= 0.60 and buy_w > sell_w:
        direction = "SUBE"
    elif align >= 0.60 and sell_w > buy_w:
        direction = "BAJA"
    else:
        direction = "ESPERAR"
        reasons.append("Temporalidades NO alineadas: lo fiable es ESPERAR.")

    conf = 40 + align * 52    # 0.6 -> ~71 ; 1.0 -> ~92
    if direction == "ESPERAR":
        conf = min(conf, 45)

    if auto_pred in ("SUBE", "BAJA") and direction in ("SUBE", "BAJA"):
        if auto_pred == direction:
            conf = min(96, conf + 8)
            reasons.append(f"Autoaprendizaje histórico confirma {direction}.")
        else:
            conf = max(0, conf - 15)
            reasons.append("Autoaprendizaje histórico discrepa: cautela.")
    if winrate is not None:
        if winrate >= 55:
            conf = min(97, conf + 5)
            reasons.append(f"Backtest: {winrate:.0f}% de acierto histórico.")
        elif 0 < winrate < 45:
            conf = max(0, conf - 8)
            reasons.append(f"Backtest bajo ({winrate:.0f}%): menos fiable.")

    action_label, icon, _ = _DIR[direction]
    act_dur = label if direction != "ESPERAR" else "—"
    act_secs = secs if direction != "ESPERAR" else 0
    return TradePlan(direction, action_label, icon, act_dur, act_secs, round(conf, 1), reasons)


def build_plan(sig, auto_pred: str | None = None, auto_conf: float | None = None,
               force_duration: tuple | None = None) -> TradePlan:
    """Genera el plan a partir de la señal del motor y (opcional) el autoaprendizaje.

    `auto_pred` es la etiqueta de analysis.auto_learn.predict (SUBE/LATERAL/BAJA).
    `force_duration` = (etiqueta, segundos): si se indica, la duración la fija el
    usuario (no se calcula por volatilidad). El motor analiza para ESA duración.
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

    # Duración: la fija el usuario si la indica; si no, se estima por volatilidad
    if force_duration:
        dur_label, dur_sec = force_duration
    else:
        price = sig.price or 1.0
        vol = (sig.atr or 0.0) / price if price else 0.0
        dur_label, dur_sec = _duration(vol, conf >= 72)
    if direction == "ESPERAR":
        dur_label, dur_sec = "—", 0

    action_label, icon, _ = _DIR[direction]
    return TradePlan(direction, action_label, icon, dur_label, dur_sec,
                     round(conf, 1), reasons)
