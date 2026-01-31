"""
Report API: given chart/bar data and strategy name, return buy/hold/sell + signal_strength.
Used by backtester (bar-by-bar) and by future 1h AI trader: call /report every 1h with current data.
"""
from __future__ import annotations

import logging
from typing import Any, Literal

import pandas as pd

from backend.strategies.indicators import atr, bollinger_bands, macd, rsi, sma

LOG = logging.getLogger(__name__)

Signal = Literal["buy", "hold", "sell"]


def _last(s: pd.Series) -> float:
    v = s.iloc[-1] if len(s) else None
    if pd.isna(v):
        return float("nan")
    return float(v)


def report_signal_mean_reversion(
    df: pd.DataFrame,
    rsi_low: int = 30,
    rsi_exit: int = 50,
    bb_window: int = 20,
    bb_std: float = 2.0,
    rsi_period: int = 14,
) -> tuple[Signal, float, dict[str, Any]]:
    """
    Compute signal from last row of df (no lookahead: indicators use only past/current).
    Returns (signal, signal_strength, snapshot).
    """
    if df is None or len(df) < bb_window:
        return "hold", 0.0, {}
    close = df["Close"]
    ub, mb, lb = bollinger_bands(close, bb_window, bb_std)
    rsi_ser = rsi(close, rsi_period)
    c, mid, r, lower = _last(close), _last(mb), _last(rsi_ser), _last(lb)
    snapshot = {"close": c, "middle_band": mid, "rsi": r, "lower_band": lower}
    if any(pd.isna(x) for x in [c, mid, r, lower]):
        return "hold", 0.0, snapshot
    if c >= mid or r > rsi_exit:
        return "sell", 0.0, snapshot
    if c <= lower and r < rsi_low:
        strength = (lower - c) / c + (rsi_low - r) / 100.0
        return "buy", strength, snapshot
    return "hold", 0.0, snapshot


def report_signal_trend_following(
    df: pd.DataFrame,
    sma_fast: int = 50,
    sma_slow: int = 200,
    macd_f: int = 12,
    macd_s: int = 26,
    macd_sig: int = 9,
) -> tuple[Signal, float, dict[str, Any]]:
    """Trend following: regime + SMA50 > SMA200 + MACD hist > 0 + SMA50 slope > 0."""
    if df is None or len(df) < sma_slow:
        return "hold", 0.0, {}
    close = df["Close"]
    s50 = sma(close, sma_fast)
    s200 = sma(close, sma_slow)
    _, _, hist = macd(close, macd_f, macd_s, macd_sig)
    c = _last(close)
    v50 = _last(s50)
    v200 = _last(s200)
    h = _last(hist)
    slope = (v50 - s50.iloc[-2]) if len(s50) >= 2 else 0.0
    snapshot = {"close": c, "sma50": v50, "sma200": v200, "macd_histogram": h, "sma50_slope": slope}
    if any(pd.isna(x) for x in [c, v50, v200, h]):
        return "hold", 0.0, snapshot
    if c < v50 or h < 0:
        return "sell", 0.0, snapshot
    if c > v200 and v50 > v200 and h > 0 and slope > 0:
        strength = (h / c) * 100 + (c - v200) / v200 if v200 else 0
        return "buy", strength, snapshot
    return "hold", 0.0, snapshot


def report_signal(strategy_name: str, df: pd.DataFrame, **kwargs: Any) -> dict[str, Any]:
    """
    Public API: given strategy name and OHLCV DataFrame (up to current bar),
    return { "signal": "buy"|"hold"|"sell", "signal_strength": float, "snapshot": dict }.
    """
    if strategy_name == "mean_reversion":
        signal, strength, snapshot = report_signal_mean_reversion(df, **kwargs)
    elif strategy_name == "trend_following":
        signal, strength, snapshot = report_signal_trend_following(df, **kwargs)
    else:
        return {"signal": "hold", "signal_strength": 0.0, "snapshot": {}, "error": f"Unknown strategy: {strategy_name}"}
    return {"signal": signal, "signal_strength": strength, "snapshot": snapshot}
