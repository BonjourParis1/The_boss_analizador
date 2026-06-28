"""
ui/theme.py — Estilo visual profesional (terminal de trading).

Estética propia (no genérica): casi-negro con un sutil degradado, acentos
verde/rojo de mercado y cian eléctrico, tipografía display 'Space Grotesk',
números monoespaciados 'JetBrains Mono' (look financiero), tarjetas con borde y
sombra suave. Evita el aspecto "plantilla de IA".
"""
from __future__ import annotations

# Paleta
BG = "#070a10"
BG2 = "#0c111b"
PANEL = "#0f1622"
PANEL_2 = "#16202f"
BORDER = "#1d2a3a"
GREEN = "#21d07a"
RED = "#ff4d5e"
BLUE = "#36c2ff"
TEXT = "#e8eef6"
MUTED = "#7e8ca3"
GOLD = "#f5b942"

CSS = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@500;700&family=Inter:wght@400;500;600&display=swap');

  :root {{
    --bg:{BG}; --panel:{PANEL}; --panel2:{PANEL_2}; --border:{BORDER};
    --green:{GREEN}; --red:{RED}; --blue:{BLUE}; --text:{TEXT}; --muted:{MUTED};
  }}

  .stApp {{
    background:
      radial-gradient(1200px 600px at 80% -10%, rgba(54,194,255,0.06), transparent 60%),
      radial-gradient(900px 500px at -10% 110%, rgba(33,208,122,0.05), transparent 55%),
      {BG};
    color:{TEXT};
    font-family:'Inter','Segoe UI',sans-serif;
  }}
  #MainMenu, footer, header {{ visibility:hidden; }}
  .block-container {{ padding-top:0.6rem; padding-bottom:1rem; max-width:100%; }}

  /* Sin atenuado/parpadeo durante auto-refrescos */
  [data-testid="stStatusWidget"] {{ display:none !important; }}
  [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"],
  .stApp, .main, .element-container, [data-testid="stVerticalBlock"],
  [data-stale="true"] {{ opacity:1 !important; filter:none !important; transition:none !important; }}

  h1,h2,h3,h4 {{ font-family:'Space Grotesk',sans-serif; color:#f2f6fb; letter-spacing:-0.2px; }}

  /* ---------- Barra lateral ---------- */
  section[data-testid="stSidebar"] {{
    background:linear-gradient(180deg,{PANEL} 0%,{BG2} 100%);
    border-right:1px solid {BORDER}; width:200px !important; min-width:200px !important;
  }}
  section[data-testid="stSidebar"] .block-container {{ padding-top:0.6rem; }}
  section[data-testid="stSidebar"] label {{ font-size:0.76rem; color:{MUTED}; margin-bottom:1px; }}
  section[data-testid="stSidebar"] .stSelectbox, section[data-testid="stSidebar"] .stToggle,
  section[data-testid="stSidebar"] .stNumberInput {{ margin-bottom:-6px; }}
  section[data-testid="stSidebar"] [data-testid="stExpander"] {{ margin-top:2px; }}

  /* ---------- Cabecera superior ---------- */
  .gx-top {{
    display:flex; align-items:center; justify-content:space-between;
    padding:10px 18px; margin:-0.6rem -1rem 12px -1rem;
    background:linear-gradient(90deg,{PANEL} 0%,{BG2} 100%);
    border-bottom:1px solid {BORDER};
  }}
  .gx-brand {{ display:flex; align-items:center; gap:10px; }}
  .gx-brand .logo {{ font-size:1.25rem; font-weight:700; font-family:'Space Grotesk';
    background:linear-gradient(90deg,{BLUE},{GREEN}); -webkit-background-clip:text;
    -webkit-text-fill-color:transparent; }}
  .gx-pill {{ font-size:0.72rem; font-weight:700; padding:4px 10px; border-radius:999px;
    border:1px solid {BORDER}; color:{MUTED}; }}
  .gx-pill.on {{ color:{GREEN}; border-color:rgba(33,208,122,0.4); background:rgba(33,208,122,0.08); }}
  .gx-pill.off {{ color:{MUTED}; }}
  .gx-clock {{ font-family:'JetBrains Mono',monospace; color:{TEXT}; font-size:0.95rem; }}

  /* ---------- Tabs estilo terminal ---------- */
  button[data-baseweb="tab"] {{ font-weight:600; color:{MUTED}; font-family:'Space Grotesk'; }}
  button[data-baseweb="tab"][aria-selected="true"] {{ color:{BLUE}; }}
  [data-baseweb="tab-highlight"] {{ background:{BLUE} !important; }}

  /* ---------- Tarjetas ---------- */
  .gx-card {{
    background:linear-gradient(180deg,{PANEL} 0%,{BG2} 100%);
    border:1px solid {BORDER}; border-radius:14px; padding:14px 16px; margin-bottom:12px;
    box-shadow:0 6px 22px rgba(0,0,0,0.35); overflow:hidden;
    word-break:break-word; overflow-wrap:anywhere;
  }}
  .gx-card * {{ overflow-wrap:anywhere; }}
  .gx-ticker {{ display:flex; align-items:baseline; gap:14px; flex-wrap:wrap; }}
  .gx-symbol {{ font-size:1.5rem; font-weight:700; font-family:'Space Grotesk'; color:#f2f6fb; }}
  .gx-price  {{ font-size:2rem; font-weight:700; font-family:'JetBrains Mono',monospace;
    letter-spacing:-1px; }}
  .gx-delta  {{ font-size:1rem; font-weight:700; font-family:'JetBrains Mono'; padding:2px 10px; border-radius:8px; }}
  .gx-up   {{ color:{GREEN}; background:rgba(33,208,122,0.12); }}
  .gx-down {{ color:{RED};   background:rgba(255,77,94,0.12); }}
  .gx-tag  {{ font-size:0.7rem; color:{MUTED}; text-transform:uppercase; letter-spacing:1.5px; font-weight:700; }}

  .gx-news {{ border-bottom:1px solid {BORDER}; padding:8px 0; }}
  .gx-news a {{ color:{TEXT}; text-decoration:none; font-size:0.9rem; }}
  .gx-news a:hover {{ color:{BLUE}; }}

  div[data-testid="stButton"] button {{ border-radius:10px; font-weight:700; border:1px solid {BORDER}; }}
  div[data-testid="stButton"] button:hover {{ border-color:{BLUE}; color:{BLUE}; }}

  /* Métricas con números monoespaciados */
  div[data-testid="stMetricValue"] {{ font-family:'JetBrains Mono',monospace; font-size:1.35rem; }}
  div[data-testid="stMetricLabel"] {{ color:{MUTED}; }}

  /* Dataframe más sobrio */
  [data-testid="stDataFrame"] {{ border:1px solid {BORDER}; border-radius:12px; }}

  /* Indicador EN VIVO pulsante */
  .gx-live {{ display:inline-flex; align-items:center; gap:6px; font-size:0.72rem;
    font-weight:700; color:{RED}; letter-spacing:1px; }}
  .gx-live .dot {{ width:9px; height:9px; border-radius:50%; background:{RED};
    animation:gxpulse 1.1s infinite; }}
  @keyframes gxpulse {{
    0% {{ box-shadow:0 0 0 0 rgba(255,77,94,0.6); }}
    70% {{ box-shadow:0 0 0 8px rgba(255,77,94,0); }}
    100% {{ box-shadow:0 0 0 0 rgba(255,77,94,0); }}
  }}
  .gx-chip {{ display:inline-block; font-size:0.74rem; font-weight:700; padding:3px 9px;
    border-radius:8px; margin:2px 4px 2px 0; }}

  /* ---------- Login premium ---------- */
  .gx-login-wrap {{ display:flex; justify-content:center; margin-top:4vh; }}
  .gx-login {{ width:min(420px,92vw); background:linear-gradient(180deg,{PANEL},{BG2});
    border:1px solid {BORDER}; border-radius:18px; padding:28px 30px;
    box-shadow:0 20px 60px rgba(0,0,0,0.5); }}
  .gx-login .logo {{ font-size:1.7rem; font-weight:700; font-family:'Space Grotesk';
    background:linear-gradient(90deg,{BLUE},{GREEN}); -webkit-background-clip:text;
    -webkit-text-fill-color:transparent; }}
</style>
"""
