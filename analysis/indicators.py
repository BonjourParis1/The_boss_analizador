"""
analysis/indicators.py — Indicadores técnicos.

Implementación propia en pandas/numpy (sin dependencias frágiles de versión).
Si tienes la librería `ta` instalada, los resultados son equivalentes.

Indicadores: RSI, MACD, medias móviles (SMA/EMA), Bandas de Bollinger, ATR.
La función `compute_all` agrega todas las columnas al DataFrame OHLCV.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Índice de Fuerza Relativa (Wilder)."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50.0)


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD, línea de señal e histograma."""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def sma(close: pd.Series, period: int) -> pd.Series:
    return close.rolling(window=period, min_periods=1).mean()


def ema(close: pd.Series, period: int) -> pd.Series:
    return close.ewm(span=period, adjust=False).mean()


def bollinger(close: pd.Series, period: int = 20, num_std: float = 2.0):
    """Bandas de Bollinger: media, banda superior e inferior."""
    mid = sma(close, period)
    std = close.rolling(window=period, min_periods=1).std(ddof=0)
    upper = mid + num_std * std
    lower = mid - num_std * std
    return mid, upper, lower


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range — mide volatilidad para stop loss / take profit."""
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ADX (Wilder): mide la FUERZA de la tendencia (0-100), no su dirección.
    <20 = mercado sin tendencia (rango/chop, señales poco fiables); >25 = tendencia clara."""
    high, low, close = df["high"], df["low"], df["close"]
    up = high.diff()
    down = -low.diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    prev_close = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close).abs(),
                    (low - prev_close).abs()], axis=1).max(axis=1)
    atr_ = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, min_periods=period,
                                adjust=False).mean() / atr_.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, min_periods=period,
                                  adjust=False).mean() / atr_.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean().fillna(0.0)


def compute_all(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega todas las columnas de indicadores a una copia del DataFrame."""
    out = df.copy()
    close = out["close"]

    out["rsi"] = rsi(close)
    macd_line, signal_line, hist = macd(close)
    out["macd"] = macd_line
    out["macd_signal"] = signal_line
    out["macd_hist"] = hist
    out["sma_fast"] = sma(close, 9)
    out["sma_slow"] = sma(close, 21)
    out["ema_50"] = ema(close, 50)
    bb_mid, bb_up, bb_low = bollinger(close)
    out["bb_mid"] = bb_mid
    out["bb_upper"] = bb_up
    out["bb_lower"] = bb_low
    out["atr"] = atr(out)
    out["adx"] = adx(out)
    return out


def snapshot_text(df) -> str:
    """Resumen compacto de indicadores de la última vela, para dárselo a la IA como
    herramientas extra de análisis (Bollinger, MACD, %b, cruces de medias, ATR)."""
    if df is None or len(df) == 0:
        return ""
    r = df.iloc[-1]
    c = float(r["close"])
    p = []
    if "rsi" in df:
        p.append(f"RSI {float(r['rsi']):.0f}")
    if "macd" in df and "macd_signal" in df:
        rel = "alcista" if r["macd"] > r["macd_signal"] else "bajista"
        p.append(f"MACD {rel} (hist {float(r.get('macd_hist', 0)):+.4f})")
    if "bb_upper" in df and "bb_lower" in df:
        bu, bl = float(r["bb_upper"]), float(r["bb_lower"])
        if c >= bu:
            p.append("precio SOBRE banda Bollinger superior (sobrecompra)")
        elif c <= bl:
            p.append("precio BAJO banda Bollinger inferior (sobreventa)")
        else:
            p.append(f"Bollinger %b {((c - bl) / (bu - bl) * 100) if bu > bl else 50:.0f}")
    if "sma_fast" in df and "sma_slow" in df:
        p.append("SMA9>SMA21 (sesgo alcista)" if r["sma_fast"] > r["sma_slow"]
                 else "SMA9<SMA21 (sesgo bajista)")
    if "ema_50" in df:
        p.append("precio sobre EMA50" if c > float(r["ema_50"]) else "precio bajo EMA50")
    if "atr" in df:
        p.append(f"ATR {float(r['atr']):.4f}")
    if "adx" in df:
        _a = float(r["adx"])
        _t = "sin tendencia (rango)" if _a < 20 else "tendencia clara" if _a > 25 else "tendencia débil"
        p.append(f"ADX {_a:.0f} ({_t})")
    return ("Indicadores actuales: " + " · ".join(p) + ".") if p else ""
