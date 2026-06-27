"""
ui/components.py — Componentes visuales profesionales (Plotly + HTML).

Estilo terminal de trading (TradingView / IQ Option):
  * ticker_header   -> símbolo, precio grande y variación coloreada.
  * pro_chart       -> velas japonesas + volumen + medias + Bollinger (crosshair).
  * indicator_panel -> RSI y MACD.
  * confidence_gauge-> medidor de confianza de la señal.
  * signal_html     -> tarjeta principal de recomendación con SL/TP.
  * news_html       -> feed de noticias con sentimiento.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.engine import BUY, SELL, Signal
from ui import theme as T

_ACT_COLOR = {BUY: T.GREEN, SELL: T.RED, "MANTENER": T.GOLD}


def _fmt(x: float) -> str:
    if x is None:
        return "—"
    ax = abs(x)
    if ax >= 1000:
        return f"{x:,.2f}"
    if ax >= 1:
        return f"{x:,.4f}".rstrip("0").rstrip(".")
    return f"{x:.6f}".rstrip("0").rstrip(".")


def ticker_header(symbol_label: str, df: pd.DataFrame, mkt_type: str) -> str:
    last = float(df["close"].iloc[-1])
    first = float(df["close"].iloc[0])
    chg = last - first
    pct = (chg / first * 100) if first else 0.0
    up = chg >= 0
    cls = "gx-up" if up else "gx-down"
    arrow = "▲" if up else "▼"
    color = T.GREEN if up else T.RED
    return f"""
    <div class="gx-card">
      <div class="gx-ticker">
        <span class="gx-symbol">{symbol_label}</span>
        <span class="gx-tag">{mkt_type.upper()}</span>
        <span class="gx-price" style="color:{color};">{_fmt(last)}</span>
        <span class="gx-delta {cls}">{arrow} {_fmt(chg)} ({pct:+.2f}%)</span>
      </div>
    </div>
    """


def pro_chart(symbol_label: str, df: pd.DataFrame) -> go.Figure:
    """Velas + volumen + SMA9/21 + EMA50 + Bandas de Bollinger, estilo TradingView."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        row_heights=[0.78, 0.22])

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        name="Precio", increasing_line_color=T.GREEN, decreasing_line_color=T.RED,
        increasing_fillcolor=T.GREEN, decreasing_fillcolor=T.RED), row=1, col=1)

    if "bb_upper" in df:
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_upper"], name="BB Sup",
                                 line=dict(color=T.MUTED, width=1, dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_lower"], name="BB Inf",
                                 line=dict(color=T.MUTED, width=1, dash="dot"),
                                 fill="tonexty", fillcolor="rgba(122,132,153,0.06)"), row=1, col=1)
    if "sma_fast" in df:
        fig.add_trace(go.Scatter(x=df.index, y=df["sma_fast"], name="SMA9",
                                 line=dict(color="#4d9fff", width=1.3)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["sma_slow"], name="SMA21",
                                 line=dict(color=T.GOLD, width=1.3)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["ema_50"], name="EMA50",
                                 line=dict(color="#b388ff", width=1.1)), row=1, col=1)

    vol_colors = [T.GREEN if c >= o else T.RED for o, c in zip(df["open"], df["close"])]
    fig.add_trace(go.Bar(x=df.index, y=df["volume"], name="Volumen",
                         marker_color=vol_colors, opacity=0.5), row=2, col=1)

    fig.update_layout(
        template="plotly_dark", height=560, paper_bgcolor=T.PANEL, plot_bgcolor=T.PANEL,
        margin=dict(l=8, r=8, t=10, b=8), xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.04, x=0, font=dict(size=10)),
        hovermode="x unified", dragmode="pan",
    )
    fig.update_xaxes(showspikes=True, spikemode="across", spikethickness=1,
                     spikecolor=T.MUTED, gridcolor="#1e2533")
    fig.update_yaxes(gridcolor="#1e2533", side="right")
    return fig


def indicator_panel(df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                        subplot_titles=("RSI (14)", "MACD"))
    fig.add_trace(go.Scatter(x=df.index, y=df["rsi"], name="RSI",
                             line=dict(color="#b388ff", width=1.4)), row=1, col=1)
    fig.add_hline(y=70, line=dict(color=T.RED, dash="dash", width=1), row=1, col=1)
    fig.add_hline(y=30, line=dict(color=T.GREEN, dash="dash", width=1), row=1, col=1)

    colors = [T.GREEN if v >= 0 else T.RED for v in df["macd_hist"]]
    fig.add_trace(go.Bar(x=df.index, y=df["macd_hist"], name="Hist", marker_color=colors), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["macd"], name="MACD",
                             line=dict(color="#4d9fff", width=1.2)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["macd_signal"], name="Señal",
                             line=dict(color=T.GOLD, width=1.2)), row=2, col=1)
    fig.update_layout(template="plotly_dark", height=320, paper_bgcolor=T.PANEL,
                      plot_bgcolor=T.PANEL, margin=dict(l=8, r=8, t=28, b=8), showlegend=False)
    fig.update_xaxes(gridcolor="#1e2533")
    fig.update_yaxes(gridcolor="#1e2533", side="right")
    return fig


def confidence_gauge(sig: Signal) -> go.Figure:
    color = _ACT_COLOR.get(sig.action, T.GOLD)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=sig.confidence,
        number={"suffix": "%", "font": {"size": 30, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": T.MUTED},
            "bar": {"color": color},
            "bgcolor": T.PANEL_2,
            "steps": [
                {"range": [0, 40], "color": "#232a3a"},
                {"range": [40, 65], "color": "#2c3447"},
                {"range": [65, 100], "color": "#384360"},
            ],
        },
    ))
    fig.update_layout(height=180, paper_bgcolor=T.PANEL, margin=dict(l=20, r=20, t=10, b=10),
                      font=dict(color=T.TEXT))
    return fig


def signal_html(sig: Signal, symbol_label: str) -> str:
    color = _ACT_COLOR.get(sig.action, T.GOLD)
    risk = ""
    if sig.stop_loss is not None:
        risk = (f"<div style='margin-top:10px;display:flex;gap:18px;font-size:0.95rem;'>"
                f"<span>🛑 SL: <b style='color:{T.RED};'>{_fmt(sig.stop_loss)}</b></span>"
                f"<span>🎯 TP: <b style='color:{T.GREEN};'>{_fmt(sig.take_profit)}</b></span></div>")
    news = ""
    if sig.news_score is not None:
        nc = T.GREEN if sig.news_score > 0.08 else T.RED if sig.news_score < -0.08 else T.MUTED
        news = f"<span style='color:{nc};'>Noticias {sig.news_score:+.2f}</span>"
    return f"""
    <div class="gx-card" style="border:2px solid {color};">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <div class="gx-tag">{symbol_label} · señal del experto</div>
          <div style="font-size:2.4rem;font-weight:800;color:{color};">{sig.icon} {sig.action}</div>
        </div>
      </div>
      <div style="margin-top:6px;display:flex;gap:18px;font-size:0.95rem;color:{T.MUTED};">
        <span>Precio <b style="color:{T.TEXT};">{_fmt(sig.price)}</b></span>
        <span>RSI <b style="color:{T.TEXT};">{sig.rsi}</b></span>
        {news}
      </div>
      {risk}
    </div>
    """


def news_html(digest) -> str:
    if not digest.items:
        return "<div class='gx-card'><span class='gx-tag'>Noticias</span><br>" \
               "<span style='color:#7a8499;'>Sin titulares recientes.</span></div>"
    head = (f"<div class='gx-tag'>Noticias &nbsp; {digest.emoji} "
            f"sentimiento {digest.label} ({digest.score:+.2f})</div>")
    rows = ""
    for it in digest.items[:8]:
        dot = T.GREEN if it.sentiment > 0.08 else T.RED if it.sentiment < -0.08 else T.MUTED
        rows += (f"<div class='gx-news'><span style='color:{dot};'>●</span> "
                 f"<a href='{it.url}' target='_blank'>{it.title}</a>"
                 f"<div style='font-size:0.72rem;color:#7a8499;'>{it.source}</div></div>")
    return f"<div class='gx-card'>{head}{rows}</div>"
