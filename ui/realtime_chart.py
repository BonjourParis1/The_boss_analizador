"""
ui/realtime_chart.py — Gráfico de streaming en TIEMPO REAL (cripto), como IQ Option.

A diferencia del gráfico Plotly (que se redibuja en cada rerun de Streamlit), este
componente se ejecuta en el NAVEGADOR: usa TradingView lightweight-charts y se conecta
directamente al WebSocket público de Binance, así la vela actual **fluctúa tick a tick**
sin recargas. Solo para criptomonedas (Binance ofrece WS público y gratuito).
"""
from __future__ import annotations

from ui import theme as T

# Intervalos válidos para el WebSocket de klines de Binance
_WS_OK = {"1s", "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h",
          "1d", "3d", "1w", "1M"}


def stream_chart_html(binance_symbol: str, interval: str = "1m", height: int = 680) -> str:
    """HTML autocontenido con el gráfico en vivo. Úsalo con st.components.v1.html."""
    iv = interval if interval in _WS_OK else "1m"
    sym = binance_symbol.upper()
    sym_l = binance_symbol.lower()
    return f"""
<div id="gxwrap" style="position:relative;">
  <div id="gxprice" style="position:absolute;top:8px;left:12px;z-index:5;
       font-family:'JetBrains Mono',monospace;font-size:1.5rem;font-weight:700;color:{T.TEXT};"></div>
  <div id="gxlive" style="position:absolute;top:10px;right:12px;z-index:5;
       font-size:0.7rem;font-weight:700;color:{T.RED};letter-spacing:1px;">● EN VIVO</div>
  <div id="gxchart" style="height:{height}px;width:100%;"></div>
</div>
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<script>
(function() {{
  const el = document.getElementById('gxchart');
  const chart = LightweightCharts.createChart(el, {{
    width: el.clientWidth, height: {height},
    layout: {{ background: {{ type:'solid', color:'{T.PANEL}' }}, textColor: '{T.TEXT}',
               fontFamily: 'JetBrains Mono, monospace' }},
    grid: {{ vertLines: {{ color:'{T.BORDER}' }}, horzLines: {{ color:'{T.BORDER}' }} }},
    timeScale: {{ timeVisible:true, secondsVisible:{str(iv.endswith('s')).lower()},
                  borderColor:'{T.BORDER}' }},
    rightPriceScale: {{ borderColor:'{T.BORDER}' }},
    crosshair: {{ mode: 0 }},
  }});
  const series = chart.addCandlestickSeries({{
    upColor:'{T.GREEN}', downColor:'{T.RED}', borderVisible:false,
    wickUpColor:'{T.GREEN}', wickDownColor:'{T.RED}' }});
  const priceEl = document.getElementById('gxprice');
  function paint(c) {{
    const up = c.close >= c.open;
    priceEl.textContent = c.close.toLocaleString(undefined, {{maximumFractionDigits:8}});
    priceEl.style.color = up ? '{T.GREEN}' : '{T.RED}';
  }}
  window.addEventListener('resize', () =>
    chart.applyOptions({{ width: el.clientWidth }}));

  // 1) Histórico inicial vía REST (Binance permite CORS en endpoints públicos)
  fetch('https://api.binance.com/api/v3/klines?symbol={sym}&interval={iv}&limit=500')
    .then(r => r.json())
    .then(d => {{
      const data = d.map(k => ({{ time:k[0]/1000, open:+k[1], high:+k[2], low:+k[3], close:+k[4] }}));
      series.setData(data);
      if (data.length) paint(data[data.length-1]);
      chart.timeScale().fitContent();
    }}).catch(()=>{{}});

  // 2) Streaming en vivo vía WebSocket (la vela actual se actualiza en cada trade)
  let ws;
  function connect() {{
    ws = new WebSocket('wss://stream.binance.com:9443/ws/{sym_l}@kline_{iv}');
    ws.onmessage = (e) => {{
      const k = JSON.parse(e.data).k;
      const c = {{ time:k.t/1000, open:+k.o, high:+k.h, low:+k.l, close:+k.c }};
      series.update(c);
      paint(c);
    }};
    ws.onclose = () => setTimeout(connect, 1500);  // reconexión automática
  }}
  connect();
}})();
</script>
"""
