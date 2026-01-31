"""Request/response shapes (for documentation)."""
from __future__ import annotations

from typing import Any


def run_request(
    ticker: str,
    interval: str,
    period_years: int,
    strategies: list[str],
    initial_cash: float,
    commission: float,
    max_entries_per_week: int,
    cooldown_days: int,
) -> dict[str, Any]:
    return {
        "ticker": ticker,
        "interval": interval,
        "period_years": period_years,
        "strategies": strategies,
        "initial_cash": initial_cash,
        "commission": commission,
        "max_entries_per_week": max_entries_per_week,
        "cooldown_days": cooldown_days,
    }
