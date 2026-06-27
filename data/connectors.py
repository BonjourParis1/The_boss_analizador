"""
data/connectors.py — Conexión a APIs públicas y legales.

Proveedores:
  * Criptomonedas -> Binance API pública (sin API key).
  * Forex -> Alpha Vantage INTRADÍA (con API key) y fallback a Yahoo Finance.
  * Acciones/índices/commodities -> Yahoo Finance (yfinance).

Todos los conectores devuelven un DataFrame OHLCV normalizado con columnas
['open','high','low','close','volume'] e índice DatetimeIndex (UTC).
Función pública: `fetch_with_retry`.
"""
from __future__ import annotations

import time

import pandas as pd
import requests

from config import Symbol, settings

_TIMEOUT = 12
_HEADERS = {"User-Agent": "GuiaExpertoTrading/2.0"}


# ----------------------------- Criptomonedas -------------------------------
_BINANCE_INTERVAL = {
    "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "12h": "12h",
    "1d": "1d", "3d": "3d", "1w": "1w", "1M": "1M",
}


def fetch_crypto(symbol: Symbol, interval: str = "5m", limit: int = 200) -> pd.DataFrame:
    """Velas de Binance. Endpoint público, sin autenticación."""
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.provider_id,
              "interval": _BINANCE_INTERVAL.get(interval, "5m"), "limit": limit}
    r = requests.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT)
    r.raise_for_status()
    df = pd.DataFrame(r.json(), columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "trades", "tbb", "tbq", "ignore"])
    df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return _finalize(df)


# --------------------------------- Forex -----------------------------------
_AV_INTERVAL = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "60min", "1d": "daily"}


def fetch_forex(symbol: Symbol, interval: str = "5m", limit: int = 200) -> pd.DataFrame:
    """Forex: Alpha Vantage intradía si hay API key; si no, Yahoo Finance."""
    base, quote = symbol.provider_id.split("/")
    if settings.alpha_vantage_key:
        try:
            return _fetch_forex_av(base, quote, interval, limit)
        except Exception:
            pass  # fallback a Yahoo Finance
    return _fetch_yf(f"{base}{quote}=X", interval, limit)


def _fetch_forex_av(base: str, quote: str, interval: str, limit: int) -> pd.DataFrame:
    """Forex con Alpha Vantage (FX_INTRADAY / FX_DAILY)."""
    av_int = _AV_INTERVAL.get(interval, "5min")
    params = {"from_symbol": base, "to_symbol": quote,
              "outputsize": "full", "apikey": settings.alpha_vantage_key}
    if av_int == "daily":
        params["function"] = "FX_DAILY"
        ts_key = "Time Series FX (Daily)"
    else:
        params["function"] = "FX_INTRADAY"
        params["interval"] = av_int
        ts_key = f"Time Series FX ({av_int})"

    r = requests.get("https://www.alphavantage.co/query", params=params,
                     headers=_HEADERS, timeout=_TIMEOUT)
    r.raise_for_status()
    payload = r.json()
    data = payload.get(ts_key)
    if not data:
        # Alpha Vantage devuelve 'Note'/'Information' al superar el límite de llamadas
        raise RuntimeError(payload.get("Note") or payload.get("Information")
                           or "Alpha Vantage sin datos")
    records = [{
        "timestamp": pd.Timestamp(ts, tz="UTC"),
        "open": float(v["1. open"]), "high": float(v["2. high"]),
        "low": float(v["3. low"]), "close": float(v["4. close"]), "volume": 0.0,
    } for ts, v in data.items()]
    df = pd.DataFrame(records).sort_values("timestamp").tail(limit)
    return _finalize(df)


# --------------------------- Acciones / índices ----------------------------
def fetch_stock(symbol: Symbol, interval: str = "5m", limit: int = 200) -> pd.DataFrame:
    return _fetch_yf(symbol.provider_id, interval, limit)


# Yahoo Finance soporta menos timeframes; mapeamos al más cercano disponible.
_YF_INTERVAL = {
    "1m": "1m", "3m": "5m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "60m", "2h": "60m", "4h": "60m", "6h": "60m", "12h": "1d",
    "1d": "1d", "3d": "1d", "1w": "1wk", "1M": "1mo",
}
_YF_PERIOD = {
    "1m": "1d", "3m": "5d", "5m": "5d", "15m": "5d", "30m": "1mo",
    "1h": "1mo", "2h": "1mo", "4h": "3mo", "6h": "3mo", "12h": "6mo",
    "1d": "1y", "3d": "2y", "1w": "5y", "1M": "10y",
}


def _fetch_yf(ticker: str, interval: str, limit: int) -> pd.DataFrame:
    """Descarga genérica de Yahoo Finance (acciones, índices, forex con =X)."""
    import yfinance as yf  # import perezoso

    df = yf.download(ticker, interval=_YF_INTERVAL.get(interval, "5m"),
                     period=_YF_PERIOD.get(interval, "5d"),
                     progress=False, auto_adjust=False)
    if df is None or df.empty:
        raise RuntimeError(f"Yahoo Finance sin datos para {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.reset_index().rename(columns={
        "Datetime": "timestamp", "Date": "timestamp", "Open": "open",
        "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    if "volume" not in df:
        df["volume"] = 0.0
    return _finalize(df.tail(limit))


# ------------------------------- Despachador -------------------------------
def fetch_ohlcv(symbol: Symbol, interval: str = "5m", limit: int = 200) -> pd.DataFrame:
    if symbol.type == "cripto":
        return fetch_crypto(symbol, interval, limit)
    if symbol.type == "forex":
        return fetch_forex(symbol, interval, limit)
    if symbol.type == "stock":
        return fetch_stock(symbol, interval, limit)
    raise ValueError(f"Tipo de símbolo no soportado: {symbol.type}")


def fetch_with_retry(symbol: Symbol, interval: str = "5m",
                     limit: int = 200, retries: int = 2) -> pd.DataFrame:
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return fetch_ohlcv(symbol, interval, limit)
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(f"No se pudo obtener datos de {symbol.label}: {last_err}")


# -------------------------------- Utilidad ---------------------------------
def _finalize(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["timestamp", "open", "high", "low", "close", "volume"]
    df = df[cols].dropna(subset=["close"]).sort_values("timestamp")
    df = df.drop_duplicates(subset=["timestamp"]).reset_index(drop=True)
    return df.set_index("timestamp")
