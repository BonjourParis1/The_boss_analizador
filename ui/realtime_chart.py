"""
ui/realtime_chart.py — Gráfico de streaming en TIEMPO REAL (cripto), estilo IQ Option.

Se ejecuta en el NAVEGADOR: TradingView lightweight-charts + WebSocket público de
Binance, así la vela actual **fluctúa en cada trade (sub-segundo)** sin recargas, con
**medias móviles superpuestas** (SMA9/SMA21), **zoom** con la rueda y precio en vivo.
Solo cripto (Binance ofrece WS público gratuito).
"""
from __future__ import annotations

from ui import theme as T

_WS_OK = {"1s", "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h",
          "1d", "3d", "1w", "1M"}


def stream_chart_html(binance_symbol: str, interval: str = "1m", height: int = 460) -> str:
    """HTML autocontenido. Úsalo con st.components.v1.html(..., height=height+20)."""
    iv = interval if interval in _WS_OK else "1m"
    sym = binance_symbol.upper()
    sym_l = binance_symbol.lower()
    secs = "true" if iv.endswith("s") else "false"
    return f"""
<div id="gxwrap" style="position:relative;background:{T.PANEL};border-radius:12px;
     border:1px solid {T.BORDER};overflow:hidden;">
  <div id="gxprice" style="position:absolute;top:8px;left:12px;z-index:5;
       font-family:'JetBrains Mono',monospace;font-size:1.6rem;font-weight:700;"></div>
  <div style="position:absolute;top:12px;right:14px;z-index:5;font-size:0.68rem;
       font-weight:700;color:{T.RED};letter-spacing:1px;">● EN VIVO</div>
  <div id="gxma" style="position:absolute;top:40px;left:12px;z-index:5;
       font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:{T.MUTED};"></div>
  <div id="gxchart" style="height:{height}px;width:100%;"></div>
</div>
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<script>
(function() {{
  const el = document.getElementById('gxchart');
  const chart = LightweightCharts.createChart(el, {{
    width: el.clientWidth, height: {height},
    layout: {{ background: {{ type:'solid', color:'{T.PANEL}' }}, textColor:'{T.TEXT}',
               fontFamily:'JetBrains Mono, monospace' }},
    grid: {{ vertLines: {{ color:'{T.BORDER}' }}, horzLines: {{ color:'{T.BORDER}' }} }},
    timeScale: {{ timeVisible:true, secondsVisible:{secs}, borderColor:'{T.BORDER}' }},
    rightPriceScale: {{ borderColor:'{T.BORDER}' }},
    crosshair: {{ mode: 0 }},
    handleScroll: true, handleScale: true,
  }});
  const candle = chart.addCandlestickSeries({{
    upColor:'{T.GREEN}', downColor:'{T.RED}', borderVisible:false,
    wickUpColor:'{T.GREEN}', wickDownColor:'{T.RED}',
    priceLineColor:'{T.MUTED}' }});
  const ma9  = chart.addLineSeries({{ color:'#4d9fff', lineWidth:2, priceLineVisible:false, lastValueVisible:false }});
  const ma21 = chart.addLineSeries({{ color:'{T.GOLD}', lineWidth:2, priceLineVisible:false, lastValueVisible:false }});
  const priceEl = document.getElementById('gxprice');
  const maEl = document.getElementById('gxma');
  let closes = [];   // [{{time, close}}]

  const smaAt = (p, i) => {{
    if (i < p-1) return null;
    let s=0; for (let j=i-p+1;j<=i;j++) s+=closes[j].close;
    return s/p;
  }};
  function rebuildMA() {{
    const m9=[], m21=[];
    for (let i=0;i<closes.length;i++) {{
      const v9=smaAt(9,i), v21=smaAt(21,i);
      if (v9!=null) m9.push({{time:closes[i].time, value:v9}});
      if (v21!=null) m21.push({{time:closes[i].time, value:v21}});
    }}
    ma9.setData(m9); ma21.setData(m21);
    if (m9.length && m21.length)
      maEl.innerHTML = "SMA9 <span style='color:#4d9fff'>"+m9[m9.length-1].value.toFixed(4)+
        "</span>  SMA21 <span style='color:{T.GOLD}'>"+m21[m21.length-1].value.toFixed(4)+"</span>";
  }}
  function paint(c) {{
    const up = c.close >= c.open;
    priceEl.textContent = c.close.toLocaleString(undefined,{{maximumFractionDigits:8}});
    priceEl.style.color = up ? '{T.GREEN}' : '{T.RED}';
  }}
  window.addEventListener('resize', () => chart.applyOptions({{ width: el.clientWidth }}));

  fetch('https://api.binance.com/api/v3/klines?symbol={sym}&interval={iv}&limit=500')
    .then(r=>r.json()).then(d=>{{
      const data=d.map(k=>({{time:k[0]/1000,open:+k[1],high:+k[2],low:+k[3],close:+k[4]}}));
      candle.setData(data);
      closes=data.map(k=>({{time:k.time, close:k.close}}));
      rebuildMA();
      if (data.length) paint(data[data.length-1]);
      chart.timeScale().fitContent();
    }}).catch(()=>{{}});

  let ws;
  function connect() {{
    ws = new WebSocket('wss://stream.binance.com:9443/ws/{sym_l}@kline_{iv}');
    ws.onmessage = (e) => {{
      const k = JSON.parse(e.data).k;
      const c = {{ time:k.t/1000, open:+k.o, high:+k.h, low:+k.l, close:+k.c }};
      candle.update(c);
      if (closes.length && closes[closes.length-1].time === c.time) closes[closes.length-1].close = c.close;
      else closes.push({{time:c.time, close:c.close}});
      // actualiza solo el último punto de cada media (eficiente)
      const i = closes.length-1;
      const v9=smaAt(9,i), v21=smaAt(21,i);
      if (v9!=null) ma9.update({{time:c.time, value:v9}});
      if (v21!=null) ma21.update({{time:c.time, value:v21}});
      paint(c);
    }};
    ws.onclose = () => setTimeout(connect, 1500);
  }}
  connect();
}})();
</script>
"""
