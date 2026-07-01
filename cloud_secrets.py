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

    # Todo lo de abajo es TOML VÁLIDO (las explicaciones van como comentarios #),
    # así puedes copiar el bloque COMPLETO y pegarlo tal cual en Secrets.
    print("# ===== Pega TODO esto en Streamlit -> Advanced settings -> Secrets =====")
    print(f'SESSION_SECRET = "{session_secret}"')
    print(f"ADMIN_KEYS_JSON = '{admin_blob}'")
    print("")
    print("# --- Cerebro IA GRATIS: Groq (recomendado) o Gemini ---")
    print('# Consigue una clave gratis (sin tarjeta) en https://console.groq.com/keys')
    print('LLM_PROVIDER = "groq"')
    print('GROQ_API_KEY = "gsk_...tu-clave-groq..."')
    print('GROQ_MODEL = "llama-3.3-70b-versatile"')
    print("# Alternativa/respaldo Gemini (opcional):")
    print('GEMINI_API_KEY = "AQ...tu-clave-gemini..."')
    print('# DEEPSEEK_API_KEY = "sk-..."   # opcional, requiere saldo')
    print("")
    print("# --- Supabase (datos en la nube) ---")
    print('SUPABASE_URL = "https://TU-PROYECTO.supabase.co"')
    print('SUPABASE_SERVICE_KEY = "eyJ...tu-service-role-key..."')
    print("")
    print("# --- Datos de mercado / noticias ---")
    print('FINNHUB_API_KEY = "..."')
    print('TWELVEDATA_API_KEY = "..."')
    print('ALPHA_VANTAGE_API_KEY = "..."')
    print('POLYGON_API_KEY = "..."   # opcional: respaldo forex/acciones (free 5/min)')
    print('YOUTUBE_API_KEY = "..."')
    print('SCAN_INTERVAL_MINUTES = "2"')
    print("")
    print("# IMPORTANTE: NO subas estos valores a GitHub (van solo aquí o en tu .env).")


if __name__ == "__main__":
    main()
