"""Cache OHLCV DataFrames as CSV keyed by (ticker, interval, period_years)."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

LOG = logging.getLogger(__name__)


def cache_path(cache_dir: str, ticker: str, interval: str, period_years: int) -> Path:
    safe = f"{ticker}_{interval}_{period_years}y".replace("=", "_").replace("/", "_")
    return Path(cache_dir) / f"{safe}.csv"


def load_cached(cache_dir: str, ticker: str, interval: str, period_years: int) -> pd.DataFrame | None:
    path = cache_path(cache_dir, ticker, interval, period_years)
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, index_col=0)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True)
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            if col not in df.columns:
                return None
        LOG.info("Loaded cached data: %s", path)
        return df
    except Exception as e:
        LOG.warning("Cache read failed %s: %s", path, e)
        return None


def save_cache(
    cache_dir: str,
    ticker: str,
    interval: str,
    period_years: int,
    df: pd.DataFrame,
) -> Path:
    path = cache_path(cache_dir, ticker, interval, period_years)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure only required columns are saved to avoid corruption
    required_cols = ["Open", "High", "Low", "Close", "Volume"]
    df_to_save = df[required_cols].copy() if all(col in df.columns for col in required_cols) else df

    # Save with index and explicit formatting
    df_to_save.to_csv(path, index=True, encoding='utf-8')
    LOG.info("Saved cache: %s", path)
    return path
