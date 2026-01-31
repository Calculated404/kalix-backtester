"""
CLI: run backtest without web UI.
  python -m kalix_backtester.cli --strategy mean_reversion --years 5
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Ensure backend is on path when run as module from project root
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from backend.config import BacktestConfig
from backend.data.loader import load_eurchf_data
from backend.engine.backtester import run_backtest
from backend.strategies import list_strategies

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)


def main() -> None:
    p = argparse.ArgumentParser(description="Run EUR/CHF backtest")
    p.add_argument("--strategy", default="mean_reversion", choices=list_strategies(), help="Strategy name")
    p.add_argument("--years", type=int, default=5, choices=(1, 2, 3, 4, 5), help="Period in years")
    p.add_argument("--cash", type=float, default=10_000, help="Initial cash")
    p.add_argument("--commission", type=float, default=0.00005, help="Commission rate")
    p.add_argument("--max-entries-per-week", type=int, default=2, help="Max new entries per week (1-4)")
    p.add_argument("--cooldown-days", type=int, default=2, help="Cooldown days after close")
    p.add_argument("--cache-dir", default="data_cache", help="Data cache directory")
    p.add_argument("--runs-dir", default="runs", help="Runs output directory")
    args = p.parse_args()

    df = load_eurchf_data(period_years=args.years, cache_dir=args.cache_dir)
    config = BacktestConfig(
        period_years=args.years,
        strategies=[args.strategy],
        initial_cash=args.cash,
        commission=args.commission,
        max_entries_per_week=min(4, max(1, args.max_entries_per_week)),
        cooldown_days=args.cooldown_days,
    )
    out = run_backtest(df, config, args.strategy, runs_dir=args.runs_dir)
    metrics = out.get("metrics", {})
    LOG.info("Metrics: %s", metrics)
    print("Win rate %%:", metrics.get("win_rate_pct"))
    print("Total return %%:", metrics.get("total_return_pct"))
    print("Max drawdown %%:", metrics.get("max_drawdown_pct"))
    print("Trades:", metrics.get("num_trades"))
    print("Run saved to:", out.get("run_path"))


if __name__ == "__main__":
    main()
