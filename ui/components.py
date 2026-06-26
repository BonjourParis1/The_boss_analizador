"""
ui/components.py — Componentes visuales reutilizables (Plotly + HTML).

* price_chart  -> velas japonesas + medias + Bandas de Bollinger.
* indicator_panel -> subgráficos de RSI y MACD.
* recommendation_card -> tarjeta con la señal (icono, confianza, riesgo, explicación).
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.engine import BUY, SELL, Signal

_COLOR = {BUY: "#16c784", SELL: "#ea3943", "MANTENER": "#f0b90b"}


def price_chart(symbol_label: str, df: pd.DataFrame) -> go.Figure:
    """Gráfico de velas con SMA9/SMA21 y Bandas de Bollinger."""
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name="Precio",
        increasing_line_color="#16c784", decreasing_line_color="#ea3943",
    ))
    if "sma_fast" in df:
        fig.add_trace(go.Scatter(x=df.index, y=df["sma_fast"], name="SMA 9",
                                 line=dict(color="#4d9fff", width=1)))
        fig.add_trace(go.Scatter(x=df.index, y=df["sma_slow"], name="SMA 21",
                                 line=dict(color="#ff9f4d", width=1)))
    if "bb_upper" in df:
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_upper"], name="BB Sup.",
                                 line=dict(color="#8b9bb4", width=1, dash="dot")))
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_lower"], name="BB Inf.",
                                 line=dict(color="#8b9bb4", width=1, dash="dot"),
                                 fill="tonexty", fillcolor="rgba(139,155,180,0.08)"))
    fig.update_layout(
        title=f"{symbol_label} — precio en tiempo real",
        template="plotly_dark", height=480, xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=1.02),
    )
    return fig


def indicator_panel(df: pd.DataFrame) -> go.Figure:
    """Subgráficos: RSI (con zonas 30/70) y MACD (histograma)."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=("RSI (14)", "MACD"))
    fig.add_trace(go.Scatter(x=df.index, y=df["rsi"], name="RSI",
                             line=dict(color="#b388ff")), row=1, col=1)
    fig.add_hline(y=70, line=dict(color="#ea3943", dash="dash"), row=1, col=1)
    fig.add_hline(y=30, line=dict(color="#16c784", dash="dash"), row=1, col=1)

    colors = ["#16c784" if v >= 0 else "#ea3943" for v in df["macd_hist"]]
    fig.add_trace(go.Bar(x=df.index, y=df["macd_hist"], name="Histograma",
                         marker_color=colors), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["macd"], name="MACD",
                             line=dict(color="#4d9fff")), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["macd_signal"], name="Señal",
                             line=dict(color="#ff9f4d")), row=2, col=1)
    fig.update_layout(template="plotly_dark", height=360,
                      margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
    return fig


def recommendation_html(sig: Signal, symbol_label: str) -> str:
    """Tarjeta HTML con la recomendación principal."""
    color = _COLOR.get(sig.action, "#f0b90b")
    riesgo = ""
    if sig.stop_loss is not None:
        riesgo = (
            f"<div style='margin-top:8px;font-size:0.9rem;'>"
            f"🛑 Stop Loss: <b>{sig.stop_loss}</b> &nbsp;|&nbsp; "
            f"🎯 Take Profit: <b>{sig.take_profit}</b></div>"
        )
    return f"""
    <div style="border:2px solid {color};border-radius:14px;padding:18px 22px;
                background:rgba(255,255,255,0.02);">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <div style="font-size:0.85rem;color:#8b9bb4;">{symbol_label}</div>
          <div style="font-size:2rem;font-weight:700;color:{color};">
            {sig.icon} {sig.action}
          </div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:0.85rem;color:#8b9bb4;">Confianza</div>
          <div style="font-size:1.6rem;font-weight:700;">{sig.confidence:.0f}%</div>
        </div>
      </div>
      <div style="margin-top:6px;font-size:0.95rem;">
        Precio actual: <b>{sig.price}</b> &nbsp;|&nbsp; RSI: <b>{sig.rsi}</b>
      </div>
      {riesgo}
    </div>
    """
