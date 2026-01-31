"""Load EUR/CHF data: use cache if present, else download and cache."""
from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from backend.data.cache import load_cached, save_cache
from backend.data.yfinance_source import download_ohlcv

LOG = logging.getLogger(__name__)

DEFAULT_TICKER = "EURCHF=X"
DEFAULT_INTERVAL = "1d"
DEFAULT_CACHE_DIR = "data_cache"


def load_eurchf_data(
    ticker: str = DEFAULT_TICKER,
    interval: str = DEFAULT_INTERVAL,
    period_years: int = 5,
    cache_dir: str = DEFAULT_CACHE_DIR,
    force_download: bool = False,
) -> pd.DataFrame:
    """
    Load OHLCV for EUR/CHF. Uses CSV cache if available.
    """
    if not force_download:
        cached = load_cached(cache_dir, ticker, interval, period_years)
        if cached is not None:
            return cached
    df = download_ohlcv(ticker, interval, period_years)
    save_cache(cache_dir, ticker, interval, period_years, df)
    return df


def ensure_eurchf_cached(
    period_years: int = 5,
    cache_dir: str = DEFAULT_CACHE_DIR,
) -> pd.DataFrame:
    """
    Preload and cache EUR/CHF data for 1--5 years on startup.
    Call this at app startup so data is ready for backtests.
    """
    return load_eurchf_data(
        ticker=DEFAULT_TICKER,
        interval=DEFAULT_INTERVAL,
        period_years=period_years,
        cache_dir=cache_dir,
        force_download=False,
    )
