"""
analysis/risk.py — Gestor de riesgo y tamaño de posición.

Decide CUÁNTO invertir en cada señal para aumentar ganancias y limitar pérdidas, a
partir de tu capital, la confianza de la señal y tu precisión histórica real.

Para opciones de pago fijo (IQ Option), el tamaño óptimo se aproxima con el criterio
de KELLY para apuestas binarias:
        f* = (p·(b+1) − 1) / b
donde p = probabilidad de acierto y b = pago (p.ej. 0.85 = 85%). Usamos KELLY
FRACCIONADO (mitad) y un TOPE de riesgo por operación para no exponer de más: así se
gana a largo plazo aguantando las rachas perdedoras. Si no hay ventaja (f*≤0), aconseja
NO invertir.
"""
from __future__ import annotations


def suggest_stake(capital: float, confidence: float, win_rate: float | None = None,
                  payout: float = 0.85, risk_cap: float = 0.05,
                  kelly_fraction: float = 0.5) -> dict:
    """Sugiere el monto a invertir en una señal.

    capital: capital disponible. confidence: confianza del plan (0-100).
    win_rate: precisión histórica real del activo (0-100) si existe (manda más que la
    confianza). payout: pago de la opción (0.85 = 85%). risk_cap: tope del % de capital
    por operación. kelly_fraction: fracción de Kelly (0.5 = medio Kelly, conservador).
    """
    capital = max(0.0, float(capital or 0))
    # Probabilidad de acierto: mezcla la confianza del plan con tu precisión real
    p = max(0.0, float(confidence or 0)) / 100.0
    if win_rate is not None:
        p = 0.45 * p + 0.55 * (float(win_rate) / 100.0)   # el historial real pesa más
    p = min(0.95, max(0.0, p))
    b = max(0.05, float(payout))

    kelly = (p * (b + 1) - 1) / b          # ventaja (edge) para pago fijo
    if capital <= 0:
        return {"stake": 0.0, "pct": 0.0, "p": round(p * 100, 1),
                "edge": round(kelly * 100, 1), "trade": False,
                "advice": "Configura tu capital para calcular la inversión sugerida."}
    if kelly <= 0:
        return {"stake": 0.0, "pct": 0.0, "p": round(p * 100, 1),
                "edge": round(kelly * 100, 1), "trade": False,
                "advice": "Sin ventaja estadística suficiente → lo profesional es NO invertir."}

    f = min(float(risk_cap), kelly * float(kelly_fraction))
    f = max(0.0, f)
    stake = round(capital * f, 2)
    return {"stake": stake, "pct": round(f * 100, 2), "p": round(p * 100, 1),
            "edge": round(kelly * 100, 1), "trade": stake > 0,
            "advice": (f"Invierte ${stake:,.2f} ({round(f * 100, 2)}% del capital). "
                       "Tamaño limitado para resistir rachas perdedoras.")}
