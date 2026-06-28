"""
ui/theme.py — Identidad visual (terminal de trading) en CLARO con fondo verde lima.

Fondo de página verde limón claro, suave y brillante; tarjetas blancas para máxima
legibilidad; acento lima; verde/rojo de mercado. Tipografías no genéricas: Manrope
(texto), Space Grotesk (títulos), JetBrains Mono (números).
"""
from __future__ import annotations

# Paleta CLARA con identidad lima
BG = "#e9f7c5"           # fondo de página: verde limón claro, suave, brillante
BG2 = "#f2fbdd"
PANEL = "#ffffff"        # tarjetas/paneles blancos (legibilidad)
PANEL_2 = "#f3f9e3"
BORDER = "#cde39e"
GREEN = "#15a34a"        # alza / compra
RED = "#e11d48"          # baja / venta
LIME = "#5aa017"         # acento (lima legible sobre claro)
BLUE = LIME              # alias retro-compatibilidad
TEXT = "#16261b"         # texto oscuro
MUTED = "#5e7560"
GOLD = "#c08a00"
GRID = "#e3eccf"         # rejilla suave para gráficos claros

CSS = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Manrope:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');

  :root {{
    --bg:{BG}; --panel:{PANEL}; --panel2:{PANEL_2}; --border:{BORDER};
    --green:{GREEN}; --red:{RED}; --lime:{LIME}; --text:{TEXT}; --muted:{MUTED};
  }}

  .stApp {{
    background:
      radial-gradient(1100px 560px at 82% -12%, rgba(140,210,60,0.22), transparent 60%),
      radial-gradient(820px 460px at -8% 110%, rgba(120,200,80,0.16), transparent 55%),
      {BG};
    color:{TEXT};
    font-family:'Manrope','Segoe UI',sans-serif;
  }}
  #MainMenu, footer, header {{ visibility:hidden; }}
  .block-container {{ padding-top:0.6rem; padding-bottom:1rem; max-width:100%; }}
  .stApp, .stApp p, .stApp span, .stApp div, .stApp label {{ color:{TEXT}; }}

  /* Sin atenuado/parpadeo durante auto-refrescos */
  [data-testid="stStatusWidget"] {{ display:none !important; }}
  [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"],
  .stApp, .main, .element-container, [data-testid="stVerticalBlock"],
  [data-stale="true"] {{ opacity:1 !important; filter:none !important; transition:none !important; }}

  h1,h2,h3,h4 {{ font-family:'Space Grotesk',sans-serif; color:#13321a; letter-spacing:-0.2px; }}

  /* ----------------- Barra lateral (clara, ordenada) ----------------- */
  section[data-testid="stSidebar"] {{
    background:linear-gradient(180deg,#f7fce9 0%,#eef7d2 100%);
    border-right:1px solid {BORDER}; width:212px !important; min-width:212px !important;
  }}
  section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {{
    padding:0 !important; min-height:0 !important; height:6px !important; }}
  section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{ padding-top:0.2rem !important; }}
  section[data-testid="stSidebar"] .block-container {{ padding:0.4rem 0.7rem 0.7rem !important; }}
  section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap:0.5rem !important; }}
  section[data-testid="stSidebar"] label {{ font-size:0.74rem; color:{MUTED}; margin-bottom:0; }}
  section[data-testid="stSidebar"] hr {{ margin:0.5rem 0 !important; border-color:{BORDER}; }}
  section[data-testid="stSidebar"] .gx-tag {{ display:block; margin:2px 0 8px; line-height:1.25; }}
  section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{ margin-bottom:0; }}
  section[data-testid="stSidebar"] div[data-testid="stButton"] {{ margin-bottom:2px; }}
  section[data-testid="stSidebar"] div[data-testid="stButton"] button {{
    min-height:34px; padding:5px 10px; font-size:0.82rem; line-height:1.15;
    text-align:left; justify-content:flex-start; border:1px solid {BORDER};
    background:#ffffff; color:{TEXT}; border-radius:9px; white-space:nowrap;
    overflow:hidden; text-overflow:ellipsis; font-family:'Manrope';
  }}
  section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {{ border-color:{LIME}; }}

  /* --------------------------- Cabecera superior --------------------------- */
  .gx-top {{
    display:flex; align-items:center; justify-content:space-between;
    padding:10px 18px; margin:-0.6rem -1rem 12px -1rem;
    background:linear-gradient(90deg,#f7fce9 0%,#eef7d2 100%);
    border-bottom:1px solid {BORDER};
  }}
  .gx-brand {{ display:flex; align-items:center; gap:10px; }}
  .gx-brand .logo {{ font-size:1.25rem; font-weight:700; font-family:'Space Grotesk';
    background:linear-gradient(90deg,{LIME},{GREEN}); -webkit-background-clip:text;
    -webkit-text-fill-color:transparent; }}
  .gx-pill {{ font-size:0.72rem; font-weight:700; padding:4px 10px; border-radius:999px;
    border:1px solid {BORDER}; color:{MUTED}; background:#ffffff; }}
  .gx-pill.on {{ color:{GREEN}; border-color:{GREEN}; background:rgba(21,163,74,0.08); }}
  .gx-clock {{ font-family:'JetBrains Mono',monospace; color:{TEXT}; font-size:0.95rem; }}

  /* ----------------------------- Tabs ----------------------------- */
  button[data-baseweb="tab"] {{ font-weight:600; color:{MUTED}; font-family:'Space Grotesk'; }}
  button[data-baseweb="tab"][aria-selected="true"] {{ color:{LIME}; }}
  [data-baseweb="tab-highlight"] {{ background:{LIME} !important; }}

  /* ----------------------------- Tarjetas ----------------------------- */
  .gx-card {{
    background:{PANEL}; border:1px solid {BORDER}; border-radius:14px;
    padding:14px 16px; margin-bottom:12px; box-shadow:0 4px 16px rgba(70,90,40,0.10);
    overflow:hidden; word-break:break-word; overflow-wrap:anywhere; color:{TEXT};
  }}
  .gx-card * {{ overflow-wrap:anywhere; }}
  .gx-ticker {{ display:flex; align-items:baseline; gap:14px; flex-wrap:wrap; }}
  .gx-symbol {{ font-size:1.5rem; font-weight:700; font-family:'Space Grotesk'; color:#13321a; }}
  .gx-price  {{ font-size:2rem; font-weight:700; font-family:'JetBrains Mono',monospace; letter-spacing:-1px; }}
  .gx-delta  {{ font-size:1rem; font-weight:700; font-family:'JetBrains Mono'; padding:2px 10px; border-radius:8px; }}
  .gx-up   {{ color:{GREEN}; background:rgba(21,163,74,0.12); }}
  .gx-down {{ color:{RED};   background:rgba(225,29,72,0.12); }}
  .gx-tag  {{ font-size:0.7rem; color:{MUTED}; text-transform:uppercase; letter-spacing:1.5px; font-weight:700; }}

  .gx-news {{ border-bottom:1px solid {BORDER}; padding:8px 0; }}
  .gx-news a {{ color:{TEXT}; text-decoration:none; font-size:0.9rem; }}
  .gx-news a:hover {{ color:{LIME}; }}

  div[data-testid="stButton"] button {{ border-radius:10px; font-weight:700;
    border:1px solid {BORDER}; background:#ffffff; color:{TEXT}; }}
  div[data-testid="stButton"] button:hover {{ border-color:{LIME}; color:{LIME}; }}

  div[data-testid="stMetricValue"] {{ font-family:'JetBrains Mono',monospace; font-size:1.35rem; color:{TEXT}; }}
  div[data-testid="stMetricLabel"] {{ color:{MUTED}; }}
  [data-testid="stDataFrame"] {{ border:1px solid {BORDER}; border-radius:12px; }}

  .gx-live {{ display:inline-flex; align-items:center; gap:6px; font-size:0.72rem;
    font-weight:700; color:{RED}; letter-spacing:1px; }}
  .gx-live .dot {{ width:9px; height:9px; border-radius:50%; background:{RED};
    animation:gxpulse 1.1s infinite; }}
  @keyframes gxpulse {{
    0% {{ box-shadow:0 0 0 0 rgba(225,29,72,0.6); }}
    70% {{ box-shadow:0 0 0 8px rgba(225,29,72,0); }}
    100% {{ box-shadow:0 0 0 0 rgba(225,29,72,0); }}
  }}
  .gx-chip {{ display:inline-block; font-size:0.74rem; font-weight:700; padding:3px 9px;
    border-radius:8px; margin:2px 4px 2px 0; }}

  .gx-login .logo {{ font-size:1.7rem; font-weight:700; font-family:'Space Grotesk';
    background:linear-gradient(90deg,{LIME},{GREEN}); -webkit-background-clip:text;
    -webkit-text-fill-color:transparent; }}
</style>
"""
