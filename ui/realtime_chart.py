"""
ui/realtime_chart.py — Gráfico de streaming en TIEMPO REAL (cripto), estilo IQ Option.

Se ejecuta en el NAVEGADOR: TradingView lightweight-charts + WebSocket público de
Binance, así la vela actual **fluctúa en cada trade (sub-segundo)** sin recargas, con
**medias móviles** (SMA9/SMA21), **zoom** (+/−/ajustar y rueda), niveles automáticos y
**hora LOCAL** del navegador (resuelve el desfase horario). Solo cripto (Binance WS).
"""
from __future__ import annotations

from ui import theme as T

_WS_OK = {"1s", "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h",
          "1d", "3d", "1w", "1M"}


def stream_chart_html(binance_symbol: str, interval: str = "1m", height: int = 560,
                      levels: list | None = None) -> str:
    """HTML autocontenido. Úsalo con st.components.v1.html(..., height=height+56)."""
    import json
    iv = interval if interval in _WS_OK else "1m"
    sym = binance_symbol.upper()
    sym_l = binance_symbol.lower()
    secs = "true" if iv.endswith("s") else "false"
    levels_json = json.dumps([{"v": l["value"], "n": l["name"], "k": l["kind"]}
                              for l in (levels or [])])
    return f"""
<div style="background:{T.PANEL};border:1px solid {T.BORDER};border-radius:12px;overflow:hidden;">
  <!-- Cabecera FUERA del área del gráfico (no obstaculiza) -->
  <div style="display:flex;align-items:center;justify-content:space-between;
              padding:8px 14px;border-bottom:1px solid {T.BORDER};">
    <div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;">
      <span id="gxprice" style="font-family:'JetBrains Mono',monospace;font-size:1.5rem;font-weight:700;"></span>
      <span id="gxma" style="font-family:'JetBrains Mono',monospace;font-size:0.74rem;color:{T.MUTED};"></span>
    </div>
    <div style="display:flex;align-items:center;gap:12px;">
      <span id="gxtz" style="font-size:0.7rem;color:{T.MUTED};"></span>
      <span style="font-size:0.68rem;font-weight:700;color:{T.RED};letter-spacing:1px;">● EN VIVO</span>
    </div>
  </div>
  <div style="position:relative;">
    <div style="position:absolute;bottom:30px;right:12px;z-index:6;display:flex;gap:6px;">
      <button id="gxzoomin"  style="cursor:pointer;width:30px;height:30px;border-radius:8px;border:1px solid {T.BORDER};background:{T.PANEL_2};color:{T.TEXT};font-size:1.1rem;">+</button>
      <button id="gxzoomout" style="cursor:pointer;width:30px;height:30px;border-radius:8px;border:1px solid {T.BORDER};background:{T.PANEL_2};color:{T.TEXT};font-size:1.1rem;">−</button>
      <button id="gxfit"     style="cursor:pointer;height:30px;padding:0 10px;border-radius:8px;border:1px solid {T.BORDER};background:{T.PANEL_2};color:{T.TEXT};font-size:0.78rem;">Ajustar</button>
    </div>
    <div id="gxchart" style="height:{height}px;width:100%;"></div>
  </div>
</div>
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<script>
(function() {{
  const el = document.getElementById('gxchart');
  // Hora LOCAL del navegador (resuelve el desfase con UTC)
  const offMin = -new Date().getTimezoneOffset();
  const offH = (offMin/60>=0?'+':'') + (offMin/60);
  document.getElementById('gxtz').textContent = 'Hora local · UTC' + offH;
  const fmtT = t => new Date(t*1000).toLocaleTimeString([], {{hour:'2-digit', minute:'2-digit', second:({secs}?'2-digit':undefined)}});

  // Al cambiar de activo el iframe se re-monta: esperamos a que la librería esté
  // cargada y a que el contenedor tenga ancho real (>0) para que el ZOOM funcione.
  function start() {{
    if (typeof LightweightCharts === 'undefined' || !el.clientWidth) {{
      return setTimeout(start, 60);
    }}
    const chart = LightweightCharts.createChart(el, {{
      width: el.clientWidth, height: {height},
      layout: {{ background: {{ type:'solid', color:'{T.PANEL}' }}, textColor:'{T.TEXT}',
                 fontFamily:'JetBrains Mono, monospace' }},
      // Fondo limpio estilo IQ Option: sin cuadrícula vertical, horizontal muy tenue
      grid: {{ vertLines: {{ visible:false }}, horzLines: {{ color:'rgba(0,0,0,0.06)' }} }},
      timeScale: {{ timeVisible:true, secondsVisible:{secs}, borderColor:'{T.BORDER}',
                    rightOffset:4, tickMarkFormatter:(t)=>fmtT(t) }},
      rightPriceScale: {{ borderColor:'{T.BORDER}' }},
      localization: {{ timeFormatter:(t)=>new Date(t*1000).toLocaleString() }},
      crosshair: {{ mode: 0 }},
      handleScroll: {{ mouseWheel:true, pressedMouseMove:true, horzTouchDrag:true, vertTouchDrag:true }},
      handleScale: {{ mouseWheel:true, pinch:true, axisPressedMouseMove:true, axisDoubleClickReset:true }},
    }});
    const candle = chart.addCandlestickSeries({{
      upColor:'{T.GREEN}', downColor:'{T.RED}', borderVisible:false,
      wickUpColor:'{T.GREEN}', wickDownColor:'{T.RED}', priceLineColor:'{T.MUTED}' }});
    const ma9  = chart.addLineSeries({{ color:'#5aa017', lineWidth:2, priceLineVisible:false, lastValueVisible:false }});
    const ma21 = chart.addLineSeries({{ color:'{T.GOLD}', lineWidth:2, priceLineVisible:false, lastValueVisible:false }});

    const LEVELS = {levels_json};
    LEVELS.forEach(l => candle.createPriceLine({{
      price:l.v, color:l.k==='res'?'{T.RED}':'{T.GREEN}', lineWidth:1, lineStyle:2,
      axisLabelVisible:true, title:l.n }}));

    const priceEl = document.getElementById('gxprice');
    const maEl = document.getElementById('gxma');
    let closes = [];
    const smaAt = (p,i) => {{ if (i<p-1) return null; let s=0; for(let j=i-p+1;j<=i;j++) s+=closes[j].close; return s/p; }};
    function rebuildMA() {{
      const m9=[], m21=[];
      for (let i=0;i<closes.length;i++) {{ const a=smaAt(9,i), b=smaAt(21,i);
        if(a!=null) m9.push({{time:closes[i].time,value:a}}); if(b!=null) m21.push({{time:closes[i].time,value:b}}); }}
      ma9.setData(m9); ma21.setData(m21);
      if (m9.length&&m21.length) maEl.innerHTML="SMA9 <span style='color:#5aa017'>"+m9[m9.length-1].value.toFixed(4)+
        "</span>  SMA21 <span style='color:{T.GOLD}'>"+m21[m21.length-1].value.toFixed(4)+"</span>";
    }}
    function paint(c) {{ const up=c.close>=c.open;
      priceEl.textContent=c.close.toLocaleString(undefined,{{maximumFractionDigits:8}});
      priceEl.style.color=up?'{T.GREEN}':'{T.RED}'; }}

    // Mantener el ancho correcto aunque el contenedor cambie de tamaño (re-montajes)
    const fixW = () => {{ if (el.clientWidth) chart.applyOptions({{ width: el.clientWidth }}); }};
    window.addEventListener('resize', fixW);
    try {{ new ResizeObserver(fixW).observe(el); }} catch(e) {{}}

    const ts = chart.timeScale();
    function zoom(f) {{ const r=ts.getVisibleLogicalRange(); if(!r) return;
      const span=r.to-r.from, c=(r.to+r.from)/2, h=(span*f)/2; ts.setVisibleLogicalRange({{from:c-h,to:c+h}}); }}
    document.getElementById('gxzoomin').onclick=()=>zoom(0.6);
    document.getElementById('gxzoomout').onclick=()=>zoom(1.7);
    document.getElementById('gxfit').onclick=()=>ts.fitContent();

    fetch('https://api.binance.com/api/v3/klines?symbol={sym}&interval={iv}&limit=500')
      .then(r=>r.json()).then(d=>{{
        const data=d.map(k=>({{time:k[0]/1000,open:+k[1],high:+k[2],low:+k[3],close:+k[4]}}));
        candle.setData(data); closes=data.map(k=>({{time:k.time,close:k.close}})); rebuildMA();
        if(data.length) paint(data[data.length-1]); fixW(); chart.timeScale().fitContent();
      }}).catch(()=>{{}});

    let ws;
    function connect() {{
      ws=new WebSocket('wss://stream.binance.com:9443/ws/{sym_l}@kline_{iv}');
      ws.onmessage=(e)=>{{ const k=JSON.parse(e.data).k;
        const c={{time:k.t/1000,open:+k.o,high:+k.h,low:+k.l,close:+k.c}};
        candle.update(c);
        if(closes.length&&closes[closes.length-1].time===c.time) closes[closes.length-1].close=c.close;
        else closes.push({{time:c.time,close:c.close}});
        const i=closes.length-1, a=smaAt(9,i), b=smaAt(21,i);
        if(a!=null) ma9.update({{time:c.time,value:a}}); if(b!=null) ma21.update({{time:c.time,value:b}});
        paint(c);
      }};
      ws.onclose=()=>setTimeout(connect,1500);
    }}
    connect();
  }}
  start();
}})();
</script>
"""
