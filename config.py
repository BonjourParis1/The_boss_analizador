"""
config.py — Configuración central del sistema.

Carga variables de entorno (.env) y define los catálogos de símbolos
y parámetros por defecto. Importar `settings` y `SYMBOLS` desde aquí.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Raíz del proyecto y carga del .env (si existe)
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Carpeta de secretos (hashes de claves). Fuera de control de versiones.
SECRETS_DIR = BASE_DIR / ".secrets"
SECRETS_DIR.mkdir(exist_ok=True)
ADMIN_KEYS_FILE = SECRETS_DIR / "admin_keys.json"


@dataclass(frozen=True)
class Settings:
    """Parámetros globales leídos del entorno con valores por defecto seguros."""
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db' / 'trading.db'}")
    alpha_vantage_key: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    refresh_seconds: int = int(os.getenv("REFRESH_SECONDS", "5"))
    auth_max_attempts: int = int(os.getenv("AUTH_MAX_ATTEMPTS", "5"))
    auth_lockout_seconds: int = int(os.getenv("AUTH_LOCKOUT_SECONDS", "300"))


settings = Settings()


# ------------------------------------------------------------------
#  Catálogo de mercados soportados.
#  type: cripto | forex | stock  (define qué conector se usa)
# ------------------------------------------------------------------
@dataclass(frozen=True)
class Symbol:
    key: str           # identificador interno único
    label: str         # nombre legible en la UI
    type: str          # cripto | forex | stock
    provider_id: str   # símbolo tal y como lo pide el proveedor


SYMBOLS: list[Symbol] = [
    # --- Criptomonedas (Binance, sin API key) ---
    Symbol("BTCUSDT", "Bitcoin (BTC/USDT)", "cripto", "BTCUSDT"),
    Symbol("ETHUSDT", "Ethereum (ETH/USDT)", "cripto", "ETHUSDT"),
    Symbol("BNBUSDT", "Binance Coin (BNB/USDT)", "cripto", "BNBUSDT"),
    Symbol("SOLUSDT", "Solana (SOL/USDT)", "cripto", "SOLUSDT"),
    # --- Forex (exchangerate.host, sin API key) ---
    Symbol("EURUSD", "Euro / Dólar (EUR/USD)", "forex", "EUR/USD"),
    Symbol("GBPUSD", "Libra / Dólar (GBP/USD)", "forex", "GBP/USD"),
    Symbol("USDJPY", "Dólar / Yen (USD/JPY)", "forex", "USD/JPY"),
    # --- Acciones / índices / commodities (Yahoo Finance) ---
    Symbol("AAPL", "Apple Inc. (AAPL)", "stock", "AAPL"),
    Symbol("MSFT", "Microsoft (MSFT)", "stock", "MSFT"),
    Symbol("TSLA", "Tesla (TSLA)", "stock", "TSLA"),
    Symbol("SPY", "S&P 500 ETF (SPY)", "stock", "SPY"),
    Symbol("GC=F", "Oro / Gold Futures", "stock", "GC=F"),
]

SYMBOLS_BY_KEY: dict[str, Symbol] = {s.key: s for s in SYMBOLS}
