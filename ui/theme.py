"""
ui/theme.py — Identidad visual propia (terminal de trading, acento verde lima).

Diseño deliberado (no plantilla): base verde-carbón oscuro con un halo lima suave,
acento lima limón brillante, números monoespaciados (JetBrains Mono), titulares
'Space Grotesk' y texto 'Manrope' (evita la tipografía genérica Inter). Verde/rojo
de mercado para alza/baja.
"""
from __future__ import annotations

# Paleta — base verde-carbón con identidad lima
BG = "#070d0a"
BG2 = "#0a130d"
PANEL = "#0d1711"
PANEL_2 = "#13241a"
BORDER = "#1f3528"
GREEN = "#27df82"        # alza / compra
RED = "#ff5b6e"          # baja / venta
LIME = "#b8f25a"         # acento principal (verde limón claro, suave, brillante)
BLUE = LIME              # alias retro-compatibilidad (todo el azul pasa a lima)
TEXT = "#e8f1ea"
MUTED = "#86a08f"
GOLD = "#f4c34d"

CSS = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Manrope:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');

  :root {{
    --bg:{BG}; --panel:{PANEL}; --panel2:{PANEL_2}; --border:{BORDER};
    --green:{GREEN}; --red:{RED}; --lime:{LIME}; --text:{TEXT}; --muted:{MUTED};
  }}

  /* Fondo con identidad lima (halo suave) + base verde-carbón */
  .stApp {{
    background:
      radial-gradient(1100px 560px at 82% -12%, rgba(184,242,90,0.10), transparent 58%),
      radial-gradient(820px 460px at -8% 112%, rgba(39,223,130,0.06), transparent 55%),
      linear-gradient(180deg, {BG2} 0%, {BG} 60%);
    color:{TEXT};
    font-family:'Manrope','Segoe UI',sans-serif;
  }}
  #MainMenu, footer, header {{ visibility:hidden; }}
  .block-container {{ padding-top:0.6rem; padding-bottom:1rem; max-width:100%; }}

  /* Sin atenuado/parpadeo durante auto-refrescos */
  [data-testid="stStatusWidget"] {{ display:none !important; }}
  [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"],
  .stApp, .main, .element-container, [data-testid="stVerticalBlock"],
  [data-stale="true"] {{ opacity:1 !important; filter:none !important; transition:none !important; }}

  h1,h2,h3,h4 {{ font-family:'Space Grotesk',sans-serif; color:#f1f7f1; letter-spacing:-0.2px; }}

  /* ----------------- Barra lateral (ordenada, sin solapes) ----------------- */
  section[data-testid="stSidebar"] {{
    background:linear-gradient(180deg,{PANEL} 0%,{BG} 100%);
    border-right:1px solid {BORDER}; width:212px !important; min-width:212px !important;
  }}
  section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {{
    padding:0 !important; min-height:0 !important; height:6px !important; }}
  section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{ padding-top:0.2rem !important; }}
  section[data-testid="stSidebar"] .block-container {{ padding:0.4rem 0.7rem 0.7rem !important; }}
  section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap:0.5rem !important; }}
  section[data-testid="stSidebar"] label {{ font-size:0.74rem; color:{MUTED}; margin-bottom:0; }}
  section[data-testid="stSidebar"] hr {{ margin:0.5rem 0 !important; border-color:{BORDER}; }}
  /* Título de sección en el panel: bloque propio, sin solaparse con los botones */
  section[data-testid="stSidebar"] .gx-tag {{ display:block; margin:2px 0 8px;
    line-height:1.25; }}
  section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{ margin-bottom:0; }}
  /* Botones de watchlist: altura fija, alineados, sin superponerse */
  section[data-testid="stSidebar"] div[data-testid="stButton"] {{ margin-bottom:2px; }}
  section[data-testid="stSidebar"] div[data-testid="stButton"] button {{
    min-height:34px; padding:5px 10px; font-size:0.82rem; line-height:1.15;
    text-align:left; justify-content:flex-start; border:1px solid {BORDER};
    background:{PANEL_2}; border-radius:9px; white-space:nowrap; overflow:hidden;
    text-overflow:ellipsis; font-family:'Manrope';
  }}
  section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {{
    border-color:{LIME}; }}

  /* --------------------------- Cabecera superior --------------------------- */
  .gx-top {{
    display:flex; align-items:center; justify-content:space-between;
    padding:10px 18px; margin:-0.6rem -1rem 12px -1rem;
    background:linear-gradient(90deg,{PANEL} 0%,{BG2} 100%);
    border-bottom:1px solid {BORDER};
  }}
  .gx-brand {{ display:flex; align-items:center; gap:10px; }}
  .gx-brand .logo {{ font-size:1.25rem; font-weight:700; font-family:'Space Grotesk';
    background:linear-gradient(90deg,{LIME},{GREEN}); -webkit-background-clip:text;
    -webkit-text-fill-color:transparent; }}
  .gx-pill {{ font-size:0.72rem; font-weight:700; padding:4px 10px; border-radius:999px;
    border:1px solid {BORDER}; color:{MUTED}; }}
  .gx-pill.on {{ color:{GREEN}; border-color:rgba(39,223,130,0.4); background:rgba(39,223,130,0.08); }}
  .gx-clock {{ font-family:'JetBrains Mono',monospace; color:{TEXT}; font-size:0.95rem; }}

  /* ----------------------------- Tabs ----------------------------- */
  button[data-baseweb="tab"] {{ font-weight:600; color:{MUTED}; font-family:'Space Grotesk'; }}
  button[data-baseweb="tab"][aria-selected="true"] {{ color:{LIME}; }}
  [data-baseweb="tab-highlight"] {{ background:{LIME} !important; }}

  /* ----------------------------- Tarjetas ----------------------------- */
  .gx-card {{
    background:linear-gradient(180deg,{PANEL} 0%,{BG2} 100%);
    border:1px solid {BORDER}; border-radius:14px; padding:14px 16px; margin-bottom:12px;
    box-shadow:0 6px 22px rgba(0,0,0,0.35); overflow:hidden;
    word-break:break-word; overflow-wrap:anywhere;
  }}
  .gx-card * {{ overflow-wrap:anywhere; }}
  .gx-ticker {{ display:flex; align-items:baseline; gap:14px; flex-wrap:wrap; }}
  .gx-symbol {{ font-size:1.5rem; font-weight:700; font-family:'Space Grotesk'; color:#f1f7f1; }}
  .gx-price  {{ font-size:2rem; font-weight:700; font-family:'JetBrains Mono',monospace; letter-spacing:-1px; }}
  .gx-delta  {{ font-size:1rem; font-weight:700; font-family:'JetBrains Mono'; padding:2px 10px; border-radius:8px; }}
  .gx-up   {{ color:{GREEN}; background:rgba(39,223,130,0.12); }}
  .gx-down {{ color:{RED};   background:rgba(255,91,110,0.12); }}
  .gx-tag  {{ font-size:0.7rem; color:{MUTED}; text-transform:uppercase; letter-spacing:1.5px; font-weight:700; }}

  .gx-news {{ border-bottom:1px solid {BORDER}; padding:8px 0; }}
  .gx-news a {{ color:{TEXT}; text-decoration:none; font-size:0.9rem; }}
  .gx-news a:hover {{ color:{LIME}; }}

  div[data-testid="stButton"] button {{ border-radius:10px; font-weight:700; border:1px solid {BORDER}; }}
  div[data-testid="stButton"] button:hover {{ border-color:{LIME}; color:{LIME}; }}

  div[data-testid="stMetricValue"] {{ font-family:'JetBrains Mono',monospace; font-size:1.35rem; }}
  div[data-testid="stMetricLabel"] {{ color:{MUTED}; }}
  [data-testid="stDataFrame"] {{ border:1px solid {BORDER}; border-radius:12px; }}

  /* Indicador EN VIVO pulsante */
  .gx-live {{ display:inline-flex; align-items:center; gap:6px; font-size:0.72rem;
    font-weight:700; color:{RED}; letter-spacing:1px; }}
  .gx-live .dot {{ width:9px; height:9px; border-radius:50%; background:{RED};
    animation:gxpulse 1.1s infinite; }}
  @keyframes gxpulse {{
    0% {{ box-shadow:0 0 0 0 rgba(255,91,110,0.6); }}
    70% {{ box-shadow:0 0 0 8px rgba(255,91,110,0); }}
    100% {{ box-shadow:0 0 0 0 rgba(255,91,110,0); }}
  }}
  .gx-chip {{ display:inline-block; font-size:0.74rem; font-weight:700; padding:3px 9px;
    border-radius:8px; margin:2px 4px 2px 0; }}

  /* ----------------------------- Login premium ----------------------------- */
  .gx-login .logo {{ font-size:1.7rem; font-weight:700; font-family:'Space Grotesk';
    background:linear-gradient(90deg,{LIME},{GREEN}); -webkit-background-clip:text;
    -webkit-text-fill-color:transparent; }}
</style>
"""
