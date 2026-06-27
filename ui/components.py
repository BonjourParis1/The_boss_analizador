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


def ticker_header(symbol_label: str, df: pd.DataFrame, mkt_type: str,
                  quote: dict | None = None, updated: str = "") -> str:
    """Encabezado tipo ticker. Si `quote` (cripto en vivo) existe, usa su precio
    y variación de 24h; si no, calcula la variación sobre las velas cargadas."""
    if quote:
        last = quote["price"]
        chg = quote["change"]
        pct = quote["change_pct"]
        live_badge = "<span class='gx-live'><span class='dot'></span>EN VIVO</span>"
        period = "24h"
    else:
        last = float(df["close"].iloc[-1])
        first = float(df["close"].iloc[0])
        chg = last - first
        pct = (chg / first * 100) if first else 0.0
        live_badge = "<span class='gx-tag'>diferido</span>"
        period = "sesión"
    up = chg >= 0
    cls = "gx-up" if up else "gx-down"
    arrow = "▲" if up else "▼"
    color = T.GREEN if up else T.RED
    foot = f"<span class='gx-tag'>actualizado {updated}</span>" if updated else ""
    return f"""
    <div class="gx-card">
      <div class="gx-ticker">
        <span class="gx-symbol">{symbol_label}</span>
        <span class="gx-tag">{mkt_type.upper()}</span>
        {live_badge}
        <span class="gx-price" style="color:{color};">{_fmt(last)}</span>
        <span class="gx-delta {cls}">{arrow} {_fmt(chg)} ({pct:+.2f}%) · {period}</span>
        &nbsp; {foot}
      </div>
    </div>
    """


def pro_chart(symbol_label: str, df: pd.DataFrame,
              support: float | None = None, resistance: float | None = None) -> go.Figure:
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

    # Niveles clave detectados por la lectura de velas
    if resistance:
        fig.add_hline(y=resistance, line=dict(color=T.RED, width=1, dash="dash"),
                      annotation_text="Resistencia", annotation_position="top right",
                      annotation_font_color=T.RED, row=1, col=1)
    if support:
        fig.add_hline(y=support, line=dict(color=T.GREEN, width=1, dash="dash"),
                      annotation_text="Soporte", annotation_position="bottom right",
                      annotation_font_color=T.GREEN, row=1, col=1)

    vol_colors = [T.GREEN if c >= o else T.RED for o, c in zip(df["open"], df["close"])]
    fig.add_trace(go.Bar(x=df.index, y=df["volume"], name="Volumen",
                         marker_color=vol_colors, opacity=0.5), row=2, col=1)

    fig.update_layout(
        template="plotly_dark", height=640, paper_bgcolor=T.PANEL, plot_bgcolor=T.PANEL,
        margin=dict(l=8, r=8, t=10, b=8), xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.04, x=0, font=dict(size=10)),
        hovermode="x unified", dragmode="pan",
    )
    # Botones de zoom temporal (estilo IQ Option / TradingView)
    fig.update_xaxes(
        rangeselector=dict(
            buttons=[
                dict(count=15, label="15m", step="minute", stepmode="backward"),
                dict(count=1, label="1H", step="hour", stepmode="backward"),
                dict(count=4, label="4H", step="hour", stepmode="backward"),
                dict(count=1, label="1D", step="day", stepmode="backward"),
                dict(count=7, label="1S", step="day", stepmode="backward"),
                dict(step="all", label="Todo"),
            ],
            bgcolor=T.PANEL_2, activecolor=T.BLUE, font=dict(color=T.TEXT, size=10),
            x=0, y=1.02,
        ),
        showspikes=True, spikemode="across", spikethickness=1,
        spikecolor=T.MUTED, gridcolor="#1e2533", row=1, col=1,
    )
    fig.update_xaxes(gridcolor="#1e2533", row=2, col=1)
    fig.update_yaxes(gridcolor="#1e2533", side="right")
    return fig


def live_line_chart(symbol_label: str, ticks) -> go.Figure:
    """Gráfico de LÍNEA en vivo (tick a tick) — actualiza cada refresco.

    `ticks` es una lista de (timestamp, precio) acumulada en tiempo real.
    Da la sensación de movimiento por segundos como en IQ Option.
    """
    xs = [t for t, _ in ticks]
    ys = [p for _, p in ticks]
    up = len(ys) < 2 or ys[-1] >= ys[0]
    color = T.GREEN if up else T.RED
    fig = go.Figure(go.Scatter(
        x=xs, y=ys, mode="lines", line=dict(color=color, width=2),
        fill="tozeroy", fillcolor=("rgba(38,166,154,0.10)" if up else "rgba(239,83,80,0.10)"),
        name="Precio en vivo"))
    if ys:
        fig.add_hline(y=ys[-1], line=dict(color=color, width=1, dash="dot"))
    fig.update_layout(
        template="plotly_dark", height=640, paper_bgcolor=T.PANEL, plot_bgcolor=T.PANEL,
        margin=dict(l=8, r=8, t=10, b=8), showlegend=False, hovermode="x unified",
        title=dict(text=f"{symbol_label} · línea en vivo (ticks)", font=dict(size=12)))
    fig.update_yaxes(gridcolor="#1e2533", side="right",
                     range=[min(ys) * 0.999, max(ys) * 1.001] if ys else None)
    fig.update_xaxes(gridcolor="#1e2533")
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


def candles_html(reading) -> str:
    """Tarjeta con la 'lectura de velas': tendencia, patrones y niveles."""
    tcolor = {"alcista": T.GREEN, "bajista": T.RED, "lateral": T.MUTED}.get(reading.trend, T.MUTED)
    chips = ""
    for p in reading.patterns:
        c = T.GREEN if p.bias == "alcista" else T.RED if p.bias == "bajista" else T.MUTED
        chips += f"<span class='gx-chip' style='background:rgba(122,132,153,0.12);color:{c};'>{p.name}</span>"
    if not chips:
        chips = "<span style='color:#7a8499;font-size:0.85rem;'>Sin patrón claro en las últimas velas.</span>"
    levels = ""
    if reading.support or reading.resistance:
        levels = (f"<div style='margin-top:8px;font-size:0.85rem;color:{T.MUTED};'>"
                  f"Soporte <b style='color:{T.GREEN};'>{_fmt(reading.support)}</b> · "
                  f"Resistencia <b style='color:{T.RED};'>{_fmt(reading.resistance)}</b></div>")
    return f"""
    <div class="gx-card">
      <div class="gx-tag">Lectura de velas</div>
      <div style="margin:4px 0;">Tendencia:
        <b style="color:{tcolor};">{reading.trend.upper()}</b>
        <span style="color:#7a8499;">(fuerza {reading.trend_strength:.0%})</span></div>
      <div>{chips}</div>
      {levels}
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
