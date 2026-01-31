"""Indicator helpers (no lookahead): Bollinger, RSI, ATR, SMA, MACD."""
from __future__ import annotations

import pandas as pd


def bollinger_bands(close: pd.Series, window: int = 20, num_std: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Middle = SMA(close, window), Upper/Lower = Middle ± num_std * std(close, window)."""
    middle = close.rolling(window=window, min_periods=window).mean()
    std = close.rolling(window=window, min_periods=window).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return upper, middle, lower


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """RSI; uses only past/current bars."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """ATR(period)."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=period).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()


def macd(
    close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """MACD line, signal line, histogram (macd - signal). No lookahead."""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def double_rsi(close: pd.Series, period: int = 7) -> pd.Series:
    """Double RSI using Wilder's smoothing method."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    
    # Use exponential weighted moving average with alpha = 1/period (Wilder's method)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def heikin_ashi(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """Standard Heikin Ashi candles."""
    ha_close = (open_ + high + low + close) / 4.0
    ha_open = pd.Series(index=open_.index, dtype=float)
    ha_open.iloc[0] = (open_.iloc[0] + close.iloc[0]) / 2.0
    
    for i in range(1, len(open_)):
        ha_open.iloc[i] = (ha_open.iloc[i-1] + ha_close.iloc[i-1]) / 2.0
    
    ha_high = pd.concat([high, ha_open, ha_close], axis=1).max(axis=1)
    ha_low = pd.concat([low, ha_open, ha_close], axis=1).min(axis=1)
    
    return ha_open, ha_high, ha_low, ha_close


def smoothed_heikin_ashi(
    open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series,
    ma_period: int = 50, smoothing: int = 10
) -> tuple[pd.Series, pd.Series]:
    """Heikin Ashi Smoothed (double smoothing)."""
    # First smoothing
    so = ema(open_, ma_period)
    sh = ema(high, ma_period)
    sl = ema(low, ma_period)
    sc = ema(close, ma_period)
    
    # Compute Heikin Ashi on smoothed OHLC
    ha_open, _, _, ha_close = heikin_ashi(so, sh, sl, sc)
    
    # Second smoothing
    sha_open = ema(ha_open, smoothing)
    sha_close = ema(ha_close, smoothing)
    
    return sha_open, sha_close


def range_filter(
    high: pd.Series, low: pd.Series, close: pd.Series,
    period: int = 100, multiplier: float = 3.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Range Filter indicator.
    
    Returns:
        tuple of (filter_line, upward_counter, downward_counter)
    """
    # Use HL2 as source
    src = (high + low) / 2.0
    
    # Calculate smoothed range
    wper = (period * 2) - 1
    absdiff = src.diff().abs()
    avrng = absdiff.ewm(span=period, adjust=False).mean()
    smrng = avrng.ewm(span=wper, adjust=False).mean() * multiplier
    
    # Calculate filter line
    filt = pd.Series(index=src.index, dtype=float)
    filt.iloc[0] = src.iloc[0]
    
    for i in range(1, len(src)):
        prev = filt.iloc[i-1]
        x = src.iloc[i]
        r = smrng.iloc[i]
        
        if x > prev:
            candidate = x - r
            filt.iloc[i] = prev if candidate < prev else candidate
        else:
            candidate = x + r
            filt.iloc[i] = prev if candidate > prev else candidate
    
    # Direction counters
    upward = pd.Series(0.0, index=src.index)
    downward = pd.Series(0.0, index=src.index)
    
    for i in range(1, len(src)):
        if filt.iloc[i] > filt.iloc[i-1]:
            upward.iloc[i] = upward.iloc[i-1] + 1.0
        elif filt.iloc[i] < filt.iloc[i-1]:
            upward.iloc[i] = 0.0
        else:
            upward.iloc[i] = upward.iloc[i-1]
        
        if filt.iloc[i] < filt.iloc[i-1]:
            downward.iloc[i] = downward.iloc[i-1] + 1.0
        elif filt.iloc[i] > filt.iloc[i-1]:
            downward.iloc[i] = 0.0
        else:
            downward.iloc[i] = downward.iloc[i-1]
    
    return filt, upward, downward
