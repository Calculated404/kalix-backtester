"""Mean Reversion: Bollinger + RSI bounce, ATR stop."""
from __future__ import annotations

import pandas as pd
from backtesting import Strategy

from backend.strategies.base import register
from backend.strategies.indicators import atr, bollinger_bands, rsi


@register("mean_reversion")
class MeanReversionStrategy(Strategy):
    """Bollinger + RSI bounce. Entry: Close <= LowerBand and RSI < rsi_low. Exit: Close >= MiddleBand or RSI > rsi_exit."""

    rsi_period = 14
    rsi_low = 30
    rsi_exit = 50
    bb_window = 20
    bb_std = 2.0
    atr_period = 14
    atr_mult_sl = 1.0
    max_entries_per_week = 2
    cooldown_days = 2

    def init(self) -> None:
        # Backtesting.py gives arrays; use .s for pandas Series in indicator functions
        import pandas as pd
        c = self.data.Close.s if hasattr(self.data.Close, "s") else pd.Series(self.data.Close)
        h = self.data.High.s if hasattr(self.data.High, "s") else pd.Series(self.data.High)
        lo = self.data.Low.s if hasattr(self.data.Low, "s") else pd.Series(self.data.Low)
        ub, mb, lb = bollinger_bands(c, self.bb_window, self.bb_std)
        rsi_ser = rsi(c, self.rsi_period)
        self.upper = self.I(lambda: ub, name="BB Upper")
        self.middle = self.I(lambda: mb, name="BB Middle")
        self.lower = self.I(lambda: lb, name="BB Lower")
        self.rsi_ind = self.I(lambda: rsi_ser, name="RSI")
        atr_ser = atr(h, lo, c, self.atr_period)
        self.atr_ind = self.I(lambda: atr_ser, name="ATR")
        self._entries_this_week: dict[str, int] = {}
        self._last_close_bar: int | None = None

    def _week_key(self, i: int) -> str:
        idx = self.data.df.index
        if i < 0 or i >= len(idx):
            return ""
        ts = idx[i]
        if hasattr(ts, "isocalendar"):
            iso = ts.isocalendar()
        else:
            iso = pd.Timestamp(ts).isocalendar()
        return f"{iso.year}-W{iso.week:02d}"

    def _can_open(self, i: int) -> bool:
        count = self._entries_this_week.get(self._week_key(i), 0)
        if count >= self.max_entries_per_week:
            return False
        if self._last_close_bar is not None and self.cooldown_days > 0:
            if i - self._last_close_bar < self.cooldown_days:
                return False
        return True

    def _record_entry(self, i: int) -> None:
        k = self._week_key(i)
        self._entries_this_week[k] = self._entries_this_week.get(k, 0) + 1

    def _record_close(self, i: int) -> None:
        self._last_close_bar = i

    def _entry_signal_strength(self) -> float:
        """Larger = stronger buy signal (more oversold)."""
        close = self.data.Close[-1]
        lower = self.lower[-1]
        rsi_val = self.rsi_ind[-1]
        if pd.isna(close) or pd.isna(lower) or pd.isna(rsi_val) or lower <= 0:
            return 0.0
        band_score = (lower - close) / close
        rsi_score = (self.rsi_low - rsi_val) / 100.0
        return band_score + rsi_score

    def next(self) -> None:
        i = len(self.data.Close) - 1
        close = self.data.Close[-1]
        mid = self.middle[-1]
        rsi_val = self.rsi_ind[-1]
        lower = self.lower[-1]
        atr_val = self.atr_ind[-1]

        if any(pd.isna(x) for x in [close, mid, rsi_val, lower]):
            return

        if self.position:
            if close >= mid or rsi_val > self.rsi_exit:
                self.position.close()
                self._record_close(i)
            return

        buy_signal = close <= lower and rsi_val < self.rsi_low
        if not buy_signal or not self._can_open(i):
            return

        self._record_entry(i)
        sl = close - self.atr_mult_sl * atr_val if not pd.isna(atr_val) and atr_val > 0 else None
        tp = mid
        self.buy(sl=sl, tp=tp)
