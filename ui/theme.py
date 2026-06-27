"""
ui/theme.py — Estilo visual profesional (terminal de trading tipo TradingView/IQ Option).

Paleta:
  fondo       #0b0e16   paneles #131722 / #1c2230
  alza/verde  #26a69a   baja/rojo #ef5350   acento #2962ff   texto #d1d4dc
"""
from __future__ import annotations

# Colores reutilizables
BG = "#0b0e16"
PANEL = "#131722"
PANEL_2 = "#1c2230"
GREEN = "#26a69a"
RED = "#ef5350"
BLUE = "#2962ff"
TEXT = "#d1d4dc"
MUTED = "#7a8499"
GOLD = "#f0b90b"

CSS = f"""
<style>
  :root {{
    --bg: {BG}; --panel: {PANEL}; --panel2: {PANEL_2};
    --green: {GREEN}; --red: {RED}; --blue: {BLUE};
    --text: {TEXT}; --muted: {MUTED};
  }}
  .stApp {{ background: {BG}; color: {TEXT}; }}
  #MainMenu, footer, header {{ visibility: hidden; }}
  .block-container {{ padding-top: 1rem; padding-bottom: 1rem; max-width: 100%; }}

  section[data-testid="stSidebar"] {{
    background: {PANEL}; border-right: 1px solid #2a3142;
  }}
  h1, h2, h3, h4 {{ color: #e8eaed; font-family: 'Segoe UI', sans-serif; }}

  /* Tabs estilo terminal */
  button[data-baseweb="tab"] {{
    font-weight: 600; color: {MUTED};
  }}
  button[data-baseweb="tab"][aria-selected="true"] {{ color: {BLUE}; }}

  /* Tarjetas */
  .gx-card {{
    background: {PANEL}; border: 1px solid #2a3142; border-radius: 12px;
    padding: 16px 18px; margin-bottom: 12px;
  }}
  .gx-ticker {{
    display:flex; align-items:baseline; gap:14px; flex-wrap:wrap;
  }}
  .gx-symbol {{ font-size: 1.6rem; font-weight: 800; color:#e8eaed; }}
  .gx-price  {{ font-size: 2.2rem; font-weight: 800; letter-spacing:-1px; }}
  .gx-delta  {{ font-size: 1.05rem; font-weight: 700; padding:2px 10px; border-radius:6px; }}
  .gx-up   {{ color:{GREEN}; background: rgba(38,166,154,0.12); }}
  .gx-down {{ color:{RED};   background: rgba(239,83,80,0.12); }}
  .gx-tag  {{ font-size:0.72rem; color:{MUTED}; text-transform:uppercase; letter-spacing:1px; }}

  .gx-news {{ border-bottom:1px solid #232a3a; padding:8px 0; }}
  .gx-news a {{ color:{TEXT}; text-decoration:none; font-size:0.92rem; }}
  .gx-news a:hover {{ color:{BLUE}; }}

  /* Botones de decisión */
  div[data-testid="stButton"] button {{ border-radius:10px; font-weight:700; }}

  /* Métricas */
  div[data-testid="stMetricValue"] {{ font-size:1.4rem; }}
</style>
"""
