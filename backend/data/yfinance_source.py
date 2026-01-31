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
    out["Volume"] = df["Volume"].astype(float) if "Volume" in df.columns else 0.0
    out = out.loc[~out["Close"].isna()]
    return out
