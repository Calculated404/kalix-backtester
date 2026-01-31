"""Configuration dataclasses for backtester."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class DataConfig:
    """Data source and cache config."""

    ticker: str = "EURCHF=X"
    interval: str = "1d"
    period_years: int = 5
    cache_dir: str = "data_cache"


@dataclass
class ConstraintConfig:
    """Trade frequency and cooldown constraints."""

    max_entries_per_week: int = 2
    cooldown_days: int = 2

    def __post_init__(self) -> None:
        if not 1 <= self.max_entries_per_week <= 4:
            raise ValueError("max_entries_per_week must be between 1 and 4")
        if self.cooldown_days < 0:
            raise ValueError("cooldown_days must be >= 0")


@dataclass
class BacktestConfig:
    """Full backtest run config."""

    ticker: str = "EURCHF=X"
    interval: str = "1d"
    period_years: int = 5
    strategies: list[str] = field(default_factory=lambda: ["mean_reversion"])
    initial_cash: float = 10_000.0
    commission: float = 0.00005
    max_entries_per_week: int = 2
    cooldown_days: int = 2
    trade_on_close: bool = False

    def constraint_config(self) -> ConstraintConfig:
        return ConstraintConfig(
            max_entries_per_week=self.max_entries_per_week,
            cooldown_days=self.cooldown_days,
        )


StrategyName = Literal["mean_reversion", "trend_following"]
