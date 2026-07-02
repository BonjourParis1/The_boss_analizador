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


_IV_SECS = {"1s": 1, "1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800,
            "1h": 3600, "2h": 7200, "4h": 14400, "6h": 21600, "12h": 43200,
            "1d": 86400, "3d": 259200, "1w": 604800, "1M": 2592000}


def stream_chart_html(binance_symbol: str, interval: str = "1m", height: int = 560,
                      levels: list | None = None, use_ws: bool = True,
                      seed: list | None = None, trades: list | None = None) -> str:
    """Gráfica TradingView con TODAS las herramientas (SMA9/21, Bollinger, niveles, zoom).

    * use_ws=True (cripto): carga de Binance y actualiza tick a tick por WebSocket.
    * use_ws=False (forex/acciones/índices/materias): se siembra con `seed` (nuestras
      velas OHLC) para que la MISMA gráfica con herramientas funcione en cualquier mercado.
    * trades: operaciones a MARCAR (estilo IQ Option). Cada una: dirección, precio de
      entrada, marca de tiempo y resultado. Se dibuja una línea VERDE (compra) / ROJA
      (venta) en el precio de entrada, una flecha en la vela de entrada y, al vencer,
      su resultado (✓ acierto / ✗ fallo). Así ves si el mercado terminó por encima o
      por debajo de donde entró la señal.
    """
    import json
    iv = interval if interval in _WS_OK else "1m"
    iv_secs = _IV_SECS.get(iv, 60)
    sym = binance_symbol.upper()
    sym_l = binance_symbol.lower()
    secs = "true" if iv.endswith("s") else "false"
    use_ws_js = "true" if use_ws else "false"
    seed_json = json.dumps(seed or [])
    levels_json = json.dumps([{"v": l["value"], "n": l["name"], "k": l["kind"]}
                              for l in (levels or [])])
    trades_json = json.dumps([
        {"dir": t.get("direction"), "p": t.get("entry_price"),
         "xp": t.get("exit_price"), "t": int(t.get("entry_ts", 0)),
         "end": int(t.get("ends_ts", 0)), "st": t.get("status", "pending")}
        for t in (trades or []) if t.get("entry_price")])
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
  const USE_WS = {use_ws_js};
  const SEED = {seed_json};
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
                    rightOffset:6, barSpacing:9, minBarSpacing:3,
                    tickMarkFormatter:(t)=>fmtT(t) }},
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
    // Bandas de Bollinger (20, 2σ) — herramienta extra de análisis
    const bbU = chart.addLineSeries({{ color:'rgba(90,160,23,0.45)', lineWidth:1, lineStyle:2, priceLineVisible:false, lastValueVisible:false }});
    const bbL = chart.addLineSeries({{ color:'rgba(90,160,23,0.45)', lineWidth:1, lineStyle:2, priceLineVisible:false, lastValueVisible:false }});

    const LEVELS = {levels_json};
    LEVELS.forEach(l => candle.createPriceLine({{
      price:l.v, color:l.k==='res'?'{T.RED}':'{T.GREEN}', lineWidth:1, lineStyle:2,
      axisLabelVisible:true, title:l.n }}));

    // === Operaciones marcadas (estilo IQ Option): línea de ENTRADA + flecha + resultado ===
    const TRADES = {trades_json};
    const IVS = {iv_secs};
    const tradeMarkers = [];
    TRADES.forEach(tr => {{
      const buy = tr.dir === 'SUBE';
      const pending = tr.st === 'pending';
      const win = tr.st === 'win';
      // Color de la LÍNEA: verde compra / roja venta. Si ya venció, el color del
      // resultado (verde acierto / rojo fallo) para reforzar el aprendizaje.
      const lineColor = pending ? (buy ? '{T.GREEN}' : '{T.RED}')
                                : (win ? '{T.GREEN}' : '{T.RED}');
      // Etiqueta breve en el eje (una sola, limpia como IQ Option)
      const tag = pending ? (buy ? 'COMPRA' : 'VENTA')
                          : (win ? 'GANÓ ✓' : 'PERDIÓ ✗');
      candle.createPriceLine({{
        price: tr.p, color: lineColor, lineWidth: 2,
        lineStyle: pending ? 0 : 2, axisLabelVisible: true, title: tag }});
      // Marca discreta en la vela de ENTRADA (sin texto encima, para no saturar)
      const tt = Math.floor(tr.t / IVS) * IVS;
      tradeMarkers.push({{
        time: tt, position: buy ? 'belowBar' : 'aboveBar',
        color: lineColor, shape: buy ? 'arrowUp' : 'arrowDown',
        text: pending ? '' : (win ? '✓' : '✗') }});
    }});
    function applyMarkers() {{
      if (tradeMarkers.length) candle.setMarkers(
        tradeMarkers.slice().sort((a,b)=>a.time-b.time)); }}

    const priceEl = document.getElementById('gxprice');
    const maEl = document.getElementById('gxma');
    let closes = [];
    const smaAt = (p,i) => {{ if (i<p-1) return null; let s=0; for(let j=i-p+1;j<=i;j++) s+=closes[j].close; return s/p; }};
    const bbAt = (i) => {{ if (i<19) return null; let m=smaAt(20,i), s=0;
      for(let j=i-19;j<=i;j++) s+=(closes[j].close-m)*(closes[j].close-m);
      const sd=Math.sqrt(s/20); return {{u:m+2*sd, l:m-2*sd}}; }};
    function rebuildMA() {{
      const m9=[], m21=[], bu=[], bl=[];
      for (let i=0;i<closes.length;i++) {{ const a=smaAt(9,i), b=smaAt(21,i), bb=bbAt(i);
        if(a!=null) m9.push({{time:closes[i].time,value:a}}); if(b!=null) m21.push({{time:closes[i].time,value:b}});
        if(bb!=null) {{ bu.push({{time:closes[i].time,value:bb.u}}); bl.push({{time:closes[i].time,value:bb.l}}); }} }}
      ma9.setData(m9); ma21.setData(m21); bbU.setData(bu); bbL.setData(bl);
      if (m9.length&&m21.length) maEl.innerHTML="SMA9 <span style='color:#5aa017'>"+m9[m9.length-1].value.toFixed(4)+
        "</span>  SMA21 <span style='color:{T.GOLD}'>"+m21[m21.length-1].value.toFixed(4)+
        "</span>  <span style='color:rgba(90,160,23,0.8)'>Bollinger 20,2</span>";
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

    function applyData(data) {{
      if(!data||!data.length) return;
      candle.setData(data); closes=data.map(k=>({{time:k.time,close:k.close}})); rebuildMA();
      applyMarkers(); paint(data[data.length-1]); fixW();
      // Mostrar las últimas ~90 velas con buen ancho (no apretujar todo el histórico)
      const N=data.length; ts.setVisibleLogicalRange({{from:Math.max(0,N-90), to:N+2}});
    }}

    if (USE_WS) {{
      // Cripto: carga desde el mirror público y actualiza tick a tick por WebSocket
      fetch('https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={iv}&limit=500')
        .then(r=>r.json()).then(d=>{{
          applyData(d.map(k=>({{time:k[0]/1000,open:+k[1],high:+k[2],low:+k[3],close:+k[4]}})));
        }}).catch(()=>{{ applyData(SEED); }});
      let ws;
      function connect() {{
        ws=new WebSocket('wss://stream.binance.com:9443/ws/{sym_l}@kline_{iv}');
        ws.onmessage=(e)=>{{ const k=JSON.parse(e.data).k;
          const c={{time:k.t/1000,open:+k.o,high:+k.h,low:+k.l,close:+k.c}};
          candle.update(c);
          if(closes.length&&closes[closes.length-1].time===c.time) closes[closes.length-1].close=c.close;
          else closes.push({{time:c.time,close:c.close}});
          const i=closes.length-1, a=smaAt(9,i), b=smaAt(21,i), bb=bbAt(i);
          if(a!=null) ma9.update({{time:c.time,value:a}}); if(b!=null) ma21.update({{time:c.time,value:b}});
          if(bb!=null) {{ bbU.update({{time:c.time,value:bb.u}}); bbL.update({{time:c.time,value:bb.l}}); }}
          paint(c);
        }};
        ws.onclose=()=>setTimeout(connect,1500);
      }}
      connect();
    }} else {{
      // Otros mercados: misma gráfica con TODAS las herramientas, sembrada con nuestros datos
      applyData(SEED);
    }}
  }}
  start();
}})();
</script>
"""
