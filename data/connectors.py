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

# --- Guardián de cuota para Twelve Data (free: 8/min, 800/día) ---
import threading as _threading
from datetime import datetime as _dt, date as _date

_TD_DAILY_CAP = 750
_TD_MINUTE_CAP = 7
_td_lock = _threading.Lock()
_td_state = {"day": None, "count": 0, "minute": None, "min_count": 0}


def td_allowed() -> bool:
    """True si queda presupuesto de llamadas a Twelve Data; reserva una si sí."""
    with _td_lock:
        today, minute = _date.today(), _dt.now().strftime("%Y%m%d%H%M")
        if _td_state["day"] != today:
            _td_state.update(day=today, count=0)
        if _td_state["minute"] != minute:
            _td_state.update(minute=minute, min_count=0)
        if _td_state["count"] >= _TD_DAILY_CAP or _td_state["min_count"] >= _TD_MINUTE_CAP:
            return False
        _td_state["count"] += 1
        _td_state["min_count"] += 1
        return True


# ----------------------------- Criptomonedas -------------------------------
_BINANCE_INTERVAL = {
    "1s": "1s",
    "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "12h": "12h",
    "1d": "1d", "3d": "3d", "1w": "1w", "1M": "1M",
}


# El mirror data-api.binance.vision responde desde regiones donde api.binance.com
# está bloqueado (p.ej. servidores de EE. UU. como los de Streamlit Cloud).
_BINANCE_HOSTS = ("https://data-api.binance.vision",
                  "https://api.binance.com",
                  "https://api1.binance.com")


def fetch_crypto(symbol: Symbol, interval: str = "5m", limit: int = 200) -> pd.DataFrame:
    """Velas de Binance (endpoint público). Prueba varios hosts por geobloqueo."""
    params = {"symbol": symbol.provider_id,
              "interval": _BINANCE_INTERVAL.get(interval, "5m"), "limit": limit}
    last = None
    for base in _BINANCE_HOSTS:
        try:
            r = requests.get(base + "/api/v3/klines", params=params,
                             headers=_HEADERS, timeout=_TIMEOUT)
            r.raise_for_status()
            df = pd.DataFrame(r.json(), columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "qav", "trades", "tbb", "tbq", "ignore"])
            df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            return _finalize(df)
        except Exception as e:  # noqa: BLE001 — probamos el siguiente host
            last = e
            continue
    raise last if last else RuntimeError("Binance no disponible")


# ------------------------------- Twelve Data -------------------------------
# Free: 800 llamadas/día, 8/min. Forex/acciones intradía fiables.
_TD_INTERVAL = {
    "1m": "1min", "3m": "5min", "5m": "5min", "15m": "15min", "30m": "30min",
    "1h": "1h", "2h": "2h", "4h": "4h", "1d": "1day", "1w": "1week", "1M": "1month",
}


def _fetch_twelvedata(td_symbol: str, interval: str, limit: int) -> pd.DataFrame:
    """Velas OHLC desde Twelve Data (forex como 'EUR/USD', acciones como 'AAPL')."""
    if not td_allowed():
        raise RuntimeError("Twelve Data: límite gratuito alcanzado, usando respaldo")
    r = requests.get("https://api.twelvedata.com/time_series",
                     params={"symbol": td_symbol, "interval": _TD_INTERVAL.get(interval, "5min"),
                             "outputsize": min(limit, 5000),
                             "apikey": settings.twelvedata_api_key, "format": "JSON"},
                     headers=_HEADERS, timeout=_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "ok" or not data.get("values"):
        raise RuntimeError(data.get("message") or "Twelve Data sin datos")
    df = pd.DataFrame(data["values"])
    df["timestamp"] = pd.to_datetime(df["datetime"], utc=True)
    for col in ("open", "high", "low", "close"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["volume"] = pd.to_numeric(df.get("volume", 0), errors="coerce").fillna(0.0)
    return _finalize(df.sort_values("timestamp").tail(limit))


# --------------------------------- Forex -----------------------------------
_AV_INTERVAL = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "60min", "1d": "daily"}


def fetch_forex(symbol: Symbol, interval: str = "5m", limit: int = 200) -> pd.DataFrame:
    """Forex con cadena de respaldo robusta para que el gráfico nunca quede vacío:

        1) Alpha Vantage intradía (FX_INTRADAY)  — requiere plan que lo permita
        2) Yahoo Finance (EURUSD=X)              — gratis, a veces bloqueado
        3) Alpha Vantage diario (FX_DAILY)       — gratis y fiable (último recurso)
    """
    base, quote = symbol.provider_id.split("/")
    errors = []
    # 1) Twelve Data intradía (free, fiable) — fuente preferida si hay clave
    if settings.twelvedata_api_key:
        try:
            return _fetch_twelvedata(symbol.provider_id, interval, limit)
        except Exception as e:  # noqa: BLE001
            errors.append(f"TwelveData: {e}")
    # 2) Intradía con Alpha Vantage (si hay clave)
    if settings.alpha_vantage_key:
        try:
            return _fetch_forex_av(base, quote, interval, limit)
        except Exception as e:  # noqa: BLE001
            errors.append(f"AV intradía: {e}")
    # 3) Yahoo Finance
    try:
        return _fetch_yf(f"{base}{quote}=X", interval, limit)
    except Exception as e:  # noqa: BLE001
        errors.append(f"Yahoo: {e}")
    # 4) Diario con Alpha Vantage (gratis y fiable, último recurso)
    if settings.alpha_vantage_key:
        try:
            return _fetch_forex_av(base, quote, "1d", limit)
        except Exception as e:  # noqa: BLE001
            errors.append(f"AV diario: {e}")
    raise RuntimeError("forex sin datos · " + " | ".join(errors[-2:]))


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
    try:
        return _fetch_yf(symbol.provider_id, interval, limit)
    except Exception as e:
        # Respaldo: Twelve Data (no cubre futuros tipo GC=F, pero sí acciones/ETF)
        if settings.twelvedata_api_key and "=" not in symbol.provider_id \
                and not symbol.provider_id.startswith("^"):
            try:
                return _fetch_twelvedata(symbol.provider_id, interval, limit)
            except Exception:
                pass
        raise e


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
