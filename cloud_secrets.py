"""
cloud_secrets.py — Genera los SECRETOS para desplegar en la nube (Streamlit Cloud).

Imprime, listo para copiar y pegar en el panel de "Secrets" de tu hosting:
  * SESSION_SECRET    -> un valor aleatorio estable (sesiones que sobreviven redeploys)
  * ADMIN_KEYS_JSON   -> los HASHES de tus 3 claves (NUNCA las claves en texto)

Uso:
    python cloud_secrets.py

Requisito: haber configurado antes tus claves con  python setup_admin.py
(NO comparte tus contraseñas: solo exporta los hashes que ya estaban guardados.)
"""
from __future__ import annotations

import json
import secrets
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from config import ADMIN_KEYS_FILE


def main() -> None:
    session_secret = secrets.token_hex(32)

    if not ADMIN_KEYS_FILE.exists():
        print("⚠️  No encuentro las claves de admin. Ejecuta primero:  python setup_admin.py")
        admin_blob = '{"hashes": ["<configura primero>"], "version": 1}'
    else:
        data = json.loads(ADMIN_KEYS_FILE.read_text(encoding="utf-8"))
        admin_blob = json.dumps(data, separators=(",", ":"))

    print("\n=========== SECRETS PARA LA NUBE (Streamlit Cloud) ===========\n")
    print("Pega esto en  Settings → Secrets  (formato TOML):\n")
    print(f'SESSION_SECRET = "{session_secret}"')
    print(f"ADMIN_KEYS_JSON = '{admin_blob}'")
    print("\n# --- y tus claves de servicios (las mismas que tu .env) ---")
    print('SUPABASE_URL = "https://TU-PROYECTO.supabase.co"')
    print('SUPABASE_SERVICE_KEY = "eyJ..."')
    print('GEMINI_API_KEY = "AQ..."')
    print('DEEPSEEK_API_KEY = "sk-..."')
    print('FINNHUB_API_KEY = "..."')
    print('TWELVEDATA_API_KEY = "..."')
    print('YOUTUBE_API_KEY = "..."')
    print('ALPHA_VANTAGE_API_KEY = "..."')
    print('SCAN_INTERVAL_MINUTES = "2"')
    print("\n==============================================================")
    print("IMPORTANTE: NO subas estos valores a GitHub. Van SOLO en el panel")
    print("de Secrets del hosting (o en tu .env local, que está en .gitignore).")


if __name__ == "__main__":
    main()
