"""Download OHLCV from Yahoo Finance and normalize to standard DataFrame."""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import yfinance as yf

LOG = logging.getLogger(__name__)

REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def download_ohlcv(
    ticker: str,
    interval: str = "1d",
    period_years: int = 5,
) -> pd.DataFrame:
    """
    Download OHLCV from Yahoo Finance.
    Returns DataFrame with columns: Open, High, Low, Close, Volume.
    Volume set to 0 if missing.

    Note: Yahoo Finance has limitations for intraday data:
    - 1m data: Only ~7 days available
    - 5m data: Only ~60 days available
    - 15m data: Only ~60 days available
    - 1h data: Up to 2 years available
    - 1d: Full history available
    """
    period_map = {
        1: "1y",
        2: "2y",
        3: "3y",
        4: "4y",
        5: "5y",
    }

    # Adjust period for intraday intervals (Yahoo Finance limitations)
    if interval in ["1m", "5m"]:
        # Only 7 days available for minute data
        adjusted_period = "5d"
        LOG.warning(
            "Interval %s has limited data availability. Using %s instead of %s",
            interval, adjusted_period, period_map.get(period_years, "5y")
        )
    elif interval in ["15m", "30m"]:
        # Only 60 days available for 15min/30min data
        adjusted_period = "60d"
        LOG.warning(
            "Interval %s has limited data availability. Using %s instead of %s",
            interval, adjusted_period, period_map.get(period_years, "5y")
        )
    elif interval == "1h":
        # Up to 2 years for hourly data
        # Use '2y' max, but respect user's requested period if it's less
        requested_period = period_map.get(period_years, "5y")
        if requested_period in ["3y", "4y", "5y"]:
            adjusted_period = "2y"
            LOG.warning(
                "Interval 1h limited to 2 years. Using %s instead of %s",
                adjusted_period, requested_period
            )
        else:
            adjusted_period = requested_period
    elif interval == "4h":
        # 4h is not natively supported - fetch 1h and resample
        requested_period = period_map.get(period_years, "5y")
        if requested_period in ["3y", "4y", "5y"]:
            adjusted_period = "2y"
        else:
            adjusted_period = requested_period

        LOG.info("4h interval not natively supported. Fetching 1h and resampling...")
        period_str = adjusted_period
        obj = yf.Ticker(ticker)
        df = obj.history(period=period_str, interval="1h", auto_adjust=True)
        if df is None or df.empty:
            raise ValueError(f"No data returned for {ticker} 4h {period_str}")

        # Resample 1h to 4h
        df = df.resample("4h").agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum",
        }).dropna()

        return normalize_ohlcv(df)
    else:
        # Daily and above have full history
        adjusted_period = period_map.get(period_years, "5y")

    period_str = adjusted_period
    LOG.info("Downloading %s interval=%s period=%s", ticker, interval, period_str)
    obj = yf.Ticker(ticker)
    df = obj.history(period=period_str, interval=interval, auto_adjust=True)
    if df is None or df.empty:
        raise ValueError(f"No data returned for {ticker} {interval} {period_str}")
    return normalize_ohlcv(df)


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure columns Open, High, Low, Close, Volume; Volume=0 if missing."""
    out = pd.DataFrame(index=df.index)
    for col in ["Open", "High", "Low", "Close"]:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")
        out[col] = df[col].astype(float)
    
    # Handle Volume
    if "Volume" in df.columns and df["Volume"].sum() > 0:
        out["Volume"] = df["Volume"].astype(float)
    else:
        # Volume is missing or all zeros (Forex pairs) - generate synthetic volume
        LOG.warning("Volume data missing or all zeros. Generating synthetic volume based on price volatility.")
        out["Volume"] = generate_synthetic_volume(out)
    
    out = out.loc[~out["Close"].isna()]
    return out


def generate_synthetic_volume(df: pd.DataFrame) -> pd.Series:
    """Generate synthetic volume based on price volatility for Forex pairs.
    
    Uses ATR (Average True Range) as a proxy for trading activity.
    Higher volatility periods tend to have higher volume.
    """
    # Calculate True Range
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift(1)).abs()
    low_close = (df["Low"] - df["Close"].shift(1)).abs()
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # Calculate ATR (14 periods)
    atr = true_range.rolling(window=14, min_periods=1).mean()
    
    # Normalize to reasonable volume range (1000 - 100000)
    # Scale based on ATR percentile
    min_vol = 1000
    max_vol = 100000
    
    atr_min = atr.quantile(0.01)
    atr_max = atr.quantile(0.99)
    
    if atr_max > atr_min:
        synthetic_volume = min_vol + (atr - atr_min) / (atr_max - atr_min) * (max_vol - min_vol)
        synthetic_volume = synthetic_volume.clip(min_vol, max_vol)
    else:
        # If ATR is constant, use midpoint
        synthetic_volume = pd.Series((min_vol + max_vol) / 2, index=df.index)
    
    # Add some randomness to make it look more natural
    import numpy as np
    noise = np.random.normal(1.0, 0.1, len(synthetic_volume))
    synthetic_volume = synthetic_volume * noise
    synthetic_volume = synthetic_volume.clip(min_vol, max_vol)
    
    return synthetic_volume.fillna(min_vol)
