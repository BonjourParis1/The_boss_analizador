"""
data/connectors.py — Conexión a APIs públicas y legales.

Proveedores:
  * Criptomonedas -> Binance API pública (sin API key).
  * Forex         -> exchangerate.host (sin API key).
  * Acciones/índices/commodities -> Yahoo Finance vía yfinance.

Todos los conectores devuelven un DataFrame OHLCV normalizado con columnas:
    ['timestamp', 'open', 'high', 'low', 'close', 'volume']
y un índice DatetimeIndex.  La función pública es `fetch_ohlcv`.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import pandas as pd
import requests

from config import Symbol, settings

_TIMEOUT = 10
_HEADERS = {"User-Agent": "GuiaExpertoTrading/1.0"}


# ----------------------------- Criptomonedas -------------------------------
# Mapeo de intervalos genéricos -> formato Binance
_BINANCE_INTERVAL = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h", "1d": "1d"}


def fetch_crypto(symbol: Symbol, interval: str = "5m", limit: int = 200) -> pd.DataFrame:
    """Velas de Binance. Endpoint público, sin autenticación."""
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol.provider_id,
        "interval": _BINANCE_INTERVAL.get(interval, "5m"),
        "limit": limit,
    }
    r = requests.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT)
    r.raise_for_status()
    rows = r.json()
    df = pd.DataFrame(
        rows,
        columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "qav", "trades", "tbb", "tbq", "ignore",
        ],
    )
    df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return _finalize(df)


# --------------------------------- Forex -----------------------------------
def fetch_forex(symbol: Symbol, interval: str = "5m", limit: int = 200) -> pd.DataFrame:
    """Serie de tipo de cambio de exchangerate.host (timeframe diario).

    La API gratuita entrega cierres diarios; construimos un OHLCV aproximado
    (open=prev close, high/low alrededor del close) suficiente para indicadores.
    Para intradía real se recomienda Alpha Vantage con API key (ver fetch_forex_av).
    """
    if settings.alpha_vantage_key:
        try:
            return fetch_forex_av(symbol, limit)
        except Exception:
            pass  # cae al método sin clave

    base, quote = symbol.provider_id.split("/")
    end = datetime.now(timezone.utc).date()
    start = end - pd.Timedelta(days=limit + 10)
    url = "https://api.exchangerate.host/timeframe"
    params = {
        "source": base,
        "currencies": quote,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }
    r = requests.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT)
    r.raise_for_status()
    payload = r.json()
    quotes = payload.get("quotes") or {}
    records = []
    for day, vals in sorted(quotes.items()):
        rate = vals.get(f"{base}{quote}")
        if rate is None:
            continue
        records.append({"timestamp": pd.Timestamp(day, tz="UTC"), "close": float(rate)})
    df = pd.DataFrame(records)
    if df.empty:
        raise RuntimeError(f"Sin datos forex para {symbol.label}")
    # Construir OHLCV a partir del cierre
    df["open"] = df["close"].shift(1).fillna(df["close"])
    df["high"] = df[["open", "close"]].max(axis=1) * 1.0005
    df["low"] = df[["open", "close"]].min(axis=1) * 0.9995
    df["volume"] = 0.0
    return _finalize(df)


def fetch_forex_av(symbol: Symbol, limit: int = 200) -> pd.DataFrame:
    """Forex intradía con Alpha Vantage (requiere ALPHA_VANTAGE_API_KEY)."""
    base, quote = symbol.provider_id.split("/")
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "FX_INTRADAY",
        "from_symbol": base,
        "to_symbol": quote,
        "interval": "5min",
        "outputsize": "compact",
        "apikey": settings.alpha_vantage_key,
    }
    r = requests.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT)
    r.raise_for_status()
    data = r.json().get("Time Series FX (5min)")
    if not data:
        raise RuntimeError("Alpha Vantage no devolvió datos (¿límite de API?).")
    records = []
    for ts, vals in data.items():
        records.append({
            "timestamp": pd.Timestamp(ts, tz="UTC"),
            "open": float(vals["1. open"]),
            "high": float(vals["2. high"]),
            "low": float(vals["3. low"]),
            "close": float(vals["4. close"]),
            "volume": 0.0,
        })
    df = pd.DataFrame(records).sort_values("timestamp").tail(limit)
    return _finalize(df)


# --------------------------- Acciones / índices ----------------------------
_YF_INTERVAL = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m", "1d": "1d"}
_YF_PERIOD = {"1m": "1d", "5m": "5d", "15m": "5d", "1h": "1mo", "1d": "1y"}


def fetch_stock(symbol: Symbol, interval: str = "5m", limit: int = 200) -> pd.DataFrame:
    """Acciones/índices/commodities vía Yahoo Finance (yfinance)."""
    import yfinance as yf  # import perezoso para acelerar el arranque

    yf_interval = _YF_INTERVAL.get(interval, "5m")
    period = _YF_PERIOD.get(interval, "5d")
    df = yf.download(
        symbol.provider_id,
        interval=yf_interval,
        period=period,
        progress=False,
        auto_adjust=False,
    )
    if df is None or df.empty:
        raise RuntimeError(f"Yahoo Finance sin datos para {symbol.label}")
    # yfinance puede devolver columnas MultiIndex; las aplanamos
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.reset_index().rename(columns={
        "Datetime": "timestamp", "Date": "timestamp",
        "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Volume": "volume",
    })
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return _finalize(df.tail(limit))


# ------------------------------- Despachador -------------------------------
def fetch_ohlcv(symbol: Symbol, interval: str = "5m", limit: int = 200) -> pd.DataFrame:
    """Punto de entrada único: elige el conector según el tipo de símbolo."""
    if symbol.type == "cripto":
        return fetch_crypto(symbol, interval, limit)
    if symbol.type == "forex":
        return fetch_forex(symbol, interval, limit)
    if symbol.type == "stock":
        return fetch_stock(symbol, interval, limit)
    raise ValueError(f"Tipo de símbolo no soportado: {symbol.type}")


def fetch_with_retry(symbol: Symbol, interval: str = "5m",
                     limit: int = 200, retries: int = 2) -> pd.DataFrame:
    """Reintenta ante fallos transitorios de red/API."""
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
    """Ordena, limpia y deja columnas estándar con índice temporal."""
    cols = ["timestamp", "open", "high", "low", "close", "volume"]
    df = df[cols].dropna(subset=["close"]).sort_values("timestamp")
    df = df.drop_duplicates(subset=["timestamp"]).reset_index(drop=True)
    return df.set_index("timestamp")
