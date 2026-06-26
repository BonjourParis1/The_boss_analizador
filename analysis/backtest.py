"""
analysis/backtest.py — Backtesting de las reglas del motor sobre datos históricos.

Recorre la serie vela a vela, genera la señal con el mismo motor (engine.analyze)
y simula entradas/salidas para medir desempeño. Devuelve un resumen de métricas
y la curva de equity.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import pandas as pd

from analysis.engine import analyze, BUY, SELL


@dataclass
class BacktestResult:
    trades: int
    wins: int
    losses: int
    win_rate: float
    total_return_pct: float
    equity_curve: pd.Series
    trade_log: pd.DataFrame

    def summary(self) -> dict:
        d = asdict(self)
        d.pop("equity_curve")
        d.pop("trade_log")
        return d


def run_backtest(symbol_key: str, df_ind: pd.DataFrame,
                 warmup: int = 30, initial_equity: float = 1000.0) -> BacktestResult:
    """Estrategia simple: abre posición con la señal y cierra al stop/take o señal opuesta.

    Es una aproximación educativa, no un simulador de ejecución perfecto.
    """
    equity = initial_equity
    position = None  # dict con entry, action, stop, take
    equity_points: list[tuple] = []
    trades: list[dict] = []

    for i in range(warmup, len(df_ind)):
        window = df_ind.iloc[: i + 1]
        row = window.iloc[-1]
        price = float(row["close"])
        sig = analyze(symbol_key, window)

        # Gestión de posición abierta
        if position is not None:
            entry = position["entry"]
            if position["action"] == BUY:
                hit_stop = price <= position["stop"]
                hit_take = price >= position["take"]
                pnl_pct = (price - entry) / entry
            else:  # SELL
                hit_stop = price >= position["stop"]
                hit_take = price <= position["take"]
                pnl_pct = (entry - price) / entry

            opposite = (position["action"] == BUY and sig.action == SELL) or \
                       (position["action"] == SELL and sig.action == BUY)

            if hit_stop or hit_take or opposite:
                equity *= (1 + pnl_pct)
                trades.append({
                    "timestamp": window.index[-1],
                    "action": position["action"],
                    "entry": entry,
                    "exit": price,
                    "pnl_pct": round(pnl_pct * 100, 3),
                })
                position = None

        # Apertura de nueva posición
        if position is None and sig.action in (BUY, SELL) and sig.stop_loss and sig.take_profit:
            position = {
                "action": sig.action,
                "entry": price,
                "stop": sig.stop_loss,
                "take": sig.take_profit,
            }

        equity_points.append((window.index[-1], equity))

    trade_log = pd.DataFrame(trades)
    wins = int((trade_log["pnl_pct"] > 0).sum()) if not trade_log.empty else 0
    losses = int((trade_log["pnl_pct"] <= 0).sum()) if not trade_log.empty else 0
    n = len(trade_log)
    equity_curve = pd.Series(
        [e for _, e in equity_points],
        index=[t for t, _ in equity_points],
        name="equity",
    )
    return BacktestResult(
        trades=n,
        wins=wins,
        losses=losses,
        win_rate=round(100 * wins / n, 2) if n else 0.0,
        total_return_pct=round((equity / initial_equity - 1) * 100, 2),
        equity_curve=equity_curve,
        trade_log=trade_log,
    )
