"""Save run artifacts under runs/<timestamp>_<strategy>_<period>/."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from backend.config import BacktestConfig


def _run_dir(runs_dir: str, strategy_name: str, period_years: int) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    name = f"{ts}_{strategy_name}_{period_years}y"
    return Path(runs_dir) / name


def save_run_artifacts(
    config: BacktestConfig,
    strategy_name: str,
    stats_dict: dict[str, Any],
    trades: list[dict],
    metrics: dict[str, Any],
    runs_dir: str = "runs",
) -> Path:
    """Write config.json, metrics.json, trades.csv; return run directory path."""
    run_path = _run_dir(runs_dir, strategy_name, config.period_years)
    run_path.mkdir(parents=True, exist_ok=True)

    config_json = {
        "ticker": config.ticker,
        "interval": config.interval,
        "period_years": config.period_years,
        "strategies": config.strategies,
        "initial_cash": config.initial_cash,
        "commission": config.commission,
        "max_entries_per_week": config.max_entries_per_week,
        "cooldown_days": config.cooldown_days,
    }
    (run_path / "config.json").write_text(json.dumps(config_json, indent=2))

    (run_path / "metrics.json").write_text(json.dumps(metrics, indent=2))

    if trades:
        df = pd.DataFrame(trades)
        df.to_csv(run_path / "trades.csv", index=False)

    # Strip non-JSON-serializable from stats for saving
    stats_ser = {k: v for k, v in stats_dict.items() if not k.startswith("_")}
    for k, v in list(stats_ser.items()):
        if hasattr(v, "tolist"):
            stats_ser[k] = v.tolist()
        elif hasattr(v, "days"):
            stats_ser[k] = str(v)
    (run_path / "stats.json").write_text(json.dumps(stats_ser, indent=2, default=str))

    return run_path
