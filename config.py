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
    # --- Cerebro IA (gratis: local con Ollama, o nube con Gemini free tier) ---
    # provider: ollama | gemini | openai_compatible (Groq/Together/LM Studio/HF) | none
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    llm_model: str = os.getenv("LLM_MODEL", os.getenv("OLLAMA_MODEL", "llama3.1")).strip()
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1").rstrip("/")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    # Respaldo del cerebro cuando Gemini agota su límite (OpenAI-compatible)
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "").strip()
    # --- Datos en tiempo real adicionales (opcional) ---
    finnhub_api_key: str = os.getenv("FINNHUB_API_KEY", "").strip()
    twelvedata_api_key: str = os.getenv("TWELVEDATA_API_KEY", "").strip()
    # --- Auto-investigación / sentimiento social (opcional) ---
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "").strip()
    lunarcrush_api_key: str = os.getenv("LUNARCRUSH_API_KEY", "").strip()
    # --- Escáner autónomo ---
    scan_interval_minutes: int = int(os.getenv("SCAN_INTERVAL_MINUTES", "2"))
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

    @property
    def has_llm(self) -> bool:
        return (self.llm_provider in ("ollama", "openai_compatible", "gemini")
                or bool(self.deepseek_api_key))


settings = Settings()


# ------------------------------------------------------------------
#  Catálogo de mercados.  type: cripto | forex | stock
#  news_query: términos para buscar noticias relacionadas.
# ------------------------------------------------------------------
@dataclass(frozen=True)
class Symbol:
    key: str
    label: str
    type: str            # cripto | forex | stock  (define el conector)
    provider_id: str
    news_query: str = ""
    group: str = ""      # categoría para la UI: Cripto | Forex | Acciones | Índices | Materias


SYMBOLS: list[Symbol] = [
    # --- Criptomonedas (Binance, sin API key) ---
    Symbol("BTCUSDT", "Bitcoin", "cripto", "BTCUSDT", "Bitcoin OR BTC crypto", "Cripto"),
    Symbol("ETHUSDT", "Ethereum", "cripto", "ETHUSDT", "Ethereum OR ETH crypto", "Cripto"),
    Symbol("BNBUSDT", "BNB", "cripto", "BNBUSDT", "Binance OR BNB", "Cripto"),
    Symbol("SOLUSDT", "Solana", "cripto", "SOLUSDT", "Solana OR SOL crypto", "Cripto"),
    Symbol("XRPUSDT", "XRP", "cripto", "XRPUSDT", "XRP OR Ripple", "Cripto"),
    Symbol("ADAUSDT", "Cardano", "cripto", "ADAUSDT", "Cardano OR ADA crypto", "Cripto"),
    Symbol("DOGEUSDT", "Dogecoin", "cripto", "DOGEUSDT", "Dogecoin OR DOGE", "Cripto"),
    Symbol("AVAXUSDT", "Avalanche", "cripto", "AVAXUSDT", "Avalanche OR AVAX crypto", "Cripto"),
    Symbol("LINKUSDT", "Chainlink", "cripto", "LINKUSDT", "Chainlink OR LINK crypto", "Cripto"),
    Symbol("MATICUSDT", "Polygon", "cripto", "MATICUSDT", "Polygon OR MATIC crypto", "Cripto"),
    # --- Forex (Alpha Vantage intradía / Yahoo) ---
    Symbol("EURUSD", "EUR/USD", "forex", "EUR/USD", "euro dollar forex ECB Fed", "Forex"),
    Symbol("GBPUSD", "GBP/USD", "forex", "GBP/USD", "pound dollar forex", "Forex"),
    Symbol("USDJPY", "USD/JPY", "forex", "USD/JPY", "yen dollar forex BOJ", "Forex"),
    Symbol("AUDUSD", "AUD/USD", "forex", "AUD/USD", "australian dollar forex", "Forex"),
    Symbol("USDCAD", "USD/CAD", "forex", "USD/CAD", "canadian dollar forex", "Forex"),
    Symbol("USDCHF", "USD/CHF", "forex", "USD/CHF", "swiss franc forex", "Forex"),
    Symbol("NZDUSD", "NZD/USD", "forex", "NZD/USD", "new zealand dollar forex", "Forex"),
    Symbol("EURJPY", "EUR/JPY", "forex", "EUR/JPY", "euro yen forex", "Forex"),
    # --- Acciones (Yahoo Finance) ---
    Symbol("AAPL", "Apple", "stock", "AAPL", "Apple stock AAPL", "Acciones"),
    Symbol("MSFT", "Microsoft", "stock", "MSFT", "Microsoft stock MSFT", "Acciones"),
    Symbol("TSLA", "Tesla", "stock", "TSLA", "Tesla stock TSLA", "Acciones"),
    Symbol("NVDA", "NVIDIA", "stock", "NVDA", "Nvidia stock NVDA", "Acciones"),
    Symbol("GOOGL", "Alphabet", "stock", "GOOGL", "Google Alphabet stock", "Acciones"),
    Symbol("AMZN", "Amazon", "stock", "AMZN", "Amazon stock AMZN", "Acciones"),
    Symbol("META", "Meta", "stock", "META", "Meta Facebook stock", "Acciones"),
    Symbol("AMD", "AMD", "stock", "AMD", "AMD stock", "Acciones"),
    # --- Índices (Yahoo Finance) ---
    Symbol("SPY", "S&P 500 (SPY)", "stock", "SPY", "S&P 500 stock market", "Índices"),
    Symbol("QQQ", "Nasdaq 100 (QQQ)", "stock", "QQQ", "Nasdaq 100 index", "Índices"),
    Symbol("DIA", "Dow Jones (DIA)", "stock", "DIA", "Dow Jones index", "Índices"),
    # --- Materias primas (Yahoo Finance) ---
    Symbol("GC=F", "Oro (Gold)", "stock", "GC=F", "gold price commodity", "Materias"),
    Symbol("SI=F", "Plata (Silver)", "stock", "SI=F", "silver price commodity", "Materias"),
    Symbol("CL=F", "Petróleo (WTI)", "stock", "CL=F", "oil price WTI commodity", "Materias"),
]

SYMBOLS_BY_KEY: dict[str, Symbol] = {s.key: s for s in SYMBOLS}
GROUPS: list[str] = ["Cripto", "Forex", "Acciones", "Índices", "Materias"]
