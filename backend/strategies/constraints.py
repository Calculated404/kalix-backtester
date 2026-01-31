"""Shared constraint state for strategies: max entries per week, cooldown."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd


@dataclass
class ConstraintState:
    """Tracks entries per ISO week and bars since last close."""

    max_entries_per_week: int = 2
    cooldown_days: int = 2
    _entries_this_week: dict[str, int] = field(default_factory=dict)
    _last_close_bar: Optional[int] = None
    _current_bar: int = 0

    def can_open_new(self, bar_index: int, index_series: pd.DatetimeIndex) -> bool:
        """True if we are allowed to open a new position (cooldown and weekly cap)."""
        if bar_index < 0 or bar_index >= len(index_series):
            return False
        ts = index_series[bar_index]
        if isinstance(ts, (int, float)):
            ts = pd.Timestamp(ts)
        iso_week = ts.isocalendar()
        week_key = f"{iso_week.year}-W{iso_week.week:02d}"
        count = self._entries_this_week.get(week_key, 0)
        if count >= self.max_entries_per_week:
            return False
        if self._last_close_bar is not None and self.cooldown_days > 0:
            bars_since = bar_index - self._last_close_bar
            if bars_since < self.cooldown_days:
                return False
        return True

    def record_entry(self, bar_index: int, index_series: pd.DatetimeIndex) -> None:
        ts = index_series[bar_index]
        if hasattr(ts, "isocalendar"):
            iso_week = ts.isocalendar()
        else:
            iso_week = pd.Timestamp(ts).isocalendar()
        week_key = f"{iso_week.year}-W{iso_week.week:02d}"
        self._entries_this_week[week_key] = self._entries_this_week.get(week_key, 0) + 1

    def record_close(self, bar_index: int) -> None:
        self._last_close_bar = bar_index
