"""
config.py — Configuración central del sistema.

Carga variables de entorno (.env) y define catálogos de símbolos y parámetros.
Importar `settings` y `SYMBOLS` desde aquí.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Carpeta de secretos (hashes de claves). Fuera de control de versiones.
SECRETS_DIR = BASE_DIR / ".secrets"
SECRETS_DIR.mkdir(exist_ok=True)
ADMIN_KEYS_FILE = SECRETS_DIR / "admin_keys.json"


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    """Parámetros globales leídos del entorno con valores por defecto seguros."""
    # --- Supabase (backend por defecto) ---
    supabase_url: str = os.getenv("SUPABASE_URL", "").strip()
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    # --- Fallback SQLite si no hay Supabase configurado ---
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db' / 'trading.db'}")
    # --- Datos de mercado ---
    alpha_vantage_key: str = os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()
    # --- Noticias ---
    newsapi_key: str = os.getenv("NEWSAPI_KEY", "").strip()
    # --- Correo ---
    email_enabled: bool = _bool("EMAIL_ENABLED", False)
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    email_to: str = os.getenv("EMAIL_TO", "")
    # --- Seguridad ---
    auth_max_attempts: int = int(os.getenv("AUTH_MAX_ATTEMPTS", "5"))
    auth_lockout_seconds: int = int(os.getenv("AUTH_LOCKOUT_SECONDS", "300"))
    # --- Tiempo real ---
    refresh_seconds: int = int(os.getenv("REFRESH_SECONDS", "5"))

    @property
    def use_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_key)


settings = Settings()


# ------------------------------------------------------------------
#  Catálogo de mercados.  type: cripto | forex | stock
#  news_query: términos para buscar noticias relacionadas.
# ------------------------------------------------------------------
@dataclass(frozen=True)
class Symbol:
    key: str
    label: str
    type: str
    provider_id: str
    news_query: str = ""


SYMBOLS: list[Symbol] = [
    # --- Criptomonedas (Binance, sin API key) ---
    Symbol("BTCUSDT", "Bitcoin", "cripto", "BTCUSDT", "Bitcoin OR BTC crypto"),
    Symbol("ETHUSDT", "Ethereum", "cripto", "ETHUSDT", "Ethereum OR ETH crypto"),
    Symbol("BNBUSDT", "BNB", "cripto", "BNBUSDT", "Binance OR BNB"),
    Symbol("SOLUSDT", "Solana", "cripto", "SOLUSDT", "Solana OR SOL crypto"),
    Symbol("XRPUSDT", "XRP", "cripto", "XRPUSDT", "XRP OR Ripple"),
    # --- Forex (Alpha Vantage intradía) ---
    Symbol("EURUSD", "EUR/USD", "forex", "EUR/USD", "euro dollar forex ECB Fed"),
    Symbol("GBPUSD", "GBP/USD", "forex", "GBP/USD", "pound dollar forex"),
    Symbol("USDJPY", "USD/JPY", "forex", "USD/JPY", "yen dollar forex BOJ"),
    Symbol("AUDUSD", "AUD/USD", "forex", "AUD/USD", "australian dollar forex"),
    # --- Acciones / índices / commodities (Yahoo Finance) ---
    Symbol("AAPL", "Apple", "stock", "AAPL", "Apple stock AAPL"),
    Symbol("MSFT", "Microsoft", "stock", "MSFT", "Microsoft stock MSFT"),
    Symbol("TSLA", "Tesla", "stock", "TSLA", "Tesla stock TSLA"),
    Symbol("NVDA", "NVIDIA", "stock", "NVDA", "Nvidia stock NVDA"),
    Symbol("SPY", "S&P 500", "stock", "SPY", "S&P 500 stock market"),
    Symbol("GC=F", "Oro (Gold)", "stock", "GC=F", "gold price commodity"),
]

SYMBOLS_BY_KEY: dict[str, Symbol] = {s.key: s for s in SYMBOLS}
