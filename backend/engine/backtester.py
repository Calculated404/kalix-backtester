"""Run backtest with Backtesting.py; single position, constraints enforced in strategy."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from backtesting import Backtest

from backend.config import BacktestConfig
from backend.reporting.export import save_run_artifacts
from backend.reporting.metrics import compute_metrics
from backend.strategies.base import get_strategy_class

LOG = logging.getLogger(__name__)


def run_backtest(
    df: pd.DataFrame,
    config: BacktestConfig,
    strategy_name: str,
    runs_dir: str = "runs",
) -> dict[str, Any]:
    """
    Run backtest for one strategy. Returns stats dict, trades list, and saves artifacts.
    """
    StrategyClass = get_strategy_class(strategy_name)
    bt = Backtest(
        df,
        StrategyClass,
        cash=config.initial_cash,
        commission=config.commission,
        trade_on_close=config.trade_on_close,
        exclusive_orders=True,
        finalize_trades=True,
    )
    # Pass constraint params into strategy
    stats = bt.run(
        max_entries_per_week=config.max_entries_per_week,
        cooldown_days=config.cooldown_days,
    )
    
    # Extract indicator data from the strategy for visualization
    indicators = {}
    try:
        strategy_instance = stats._strategy if hasattr(stats, '_strategy') else None
        if strategy_instance and hasattr(strategy_instance, '_indicators'):
            ind_data = strategy_instance._indicators

            # Handle both dict and list formats
            if isinstance(ind_data, dict):
                items = ind_data.items()
            elif isinstance(ind_data, list):
                # If it's a list, create a dict with enumerated keys
                items = [(f"indicator_{i}", v) for i, v in enumerate(ind_data)]
            else:
                items = []

            for ind_name, ind_series in items:
                try:
                    if hasattr(ind_series, '__iter__') and not isinstance(ind_series, (str, dict)):
                        indicators[ind_name] = [float(v) if not pd.isna(v) else None for v in ind_series]
                    else:
                        # Single value, convert to list
                        indicators[ind_name] = [float(ind_series)] if not pd.isna(ind_series) else [None]
                except (ValueError, TypeError):
                    # Skip indicators that can't be converted
                    LOG.debug("Skipped indicator %s - couldn't convert to list", ind_name)
    except Exception as e:
        LOG.warning("Could not extract indicators: %s", e)
        indicators = {}
    stats_dict = stats if isinstance(stats, dict) else stats.to_dict()
    trades = []
    tf = getattr(stats, "_trades", None)
    if tf is not None and hasattr(tf, "iterrows"):
        try:
            cols = tf.columns.tolist()
            for _, row in tf.iterrows():
                def _get(*keys):
                    for k in keys:
                        if k in cols:
                            v = row.get(k)
                            if v is not None and not (hasattr(v, "__iter__") and not isinstance(v, str)):
                                return v
                    return None
                trades.append({
                    "entry_time": _get("EntryTime", "Entry time"),
                    "entry_price": _get("EntryPrice", "Entry price"),
                    "exit_time": _get("ExitTime", "Exit time"),
                    "exit_price": _get("ExitPrice", "Exit price"),
                    "pnl": _get("PnL") or 0,
                    "return_pct": _get("Return [%]", "ReturnPct") or 0,
                })
        except Exception as e:
            LOG.warning("Could not parse _trades: %s", e)
            
    # Pass initial_cash explicitly to ensure it's correct even if stats misses it
    metrics = compute_metrics(stats_dict, trades, initial_cash=config.initial_cash)

    run_path = save_run_artifacts(
        config=config,
        strategy_name=strategy_name,
        stats_dict=stats_dict,
        trades=trades,
        metrics=metrics,
        runs_dir=runs_dir,
    )
    return {
        "strategy": strategy_name,
        "stats": stats_dict,
        "trades": trades,
        "metrics": metrics,
        "indicators": indicators,
        "run_path": str(run_path),
        "bt": bt,
        "stats_obj": stats,
    }
