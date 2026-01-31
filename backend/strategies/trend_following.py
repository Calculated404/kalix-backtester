"""Trend Following: SMA 50/200 + MACD confirmation, ATR stop."""
from __future__ import annotations

import pandas as pd
from backtesting import Strategy

from backend.strategies.base import register
from backend.strategies.indicators import atr, macd, sma


@register("trend_following")
class TrendFollowingStrategy(Strategy):
    """Long when Close > SMA200, SMA50 > SMA200, MACD hist > 0, SMA50 slope > 0. Exit: Close < SMA50 or MACD hist < 0."""

    sma_fast = 50
    sma_slow = 200
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    atr_period = 14
    atr_mult_sl = 1.0
    max_entries_per_week = 2
    cooldown_days = 2

    def init(self) -> None:
        import pandas as pd
        c = self.data.Close.s if hasattr(self.data.Close, "s") else pd.Series(self.data.Close)
        h = self.data.High.s if hasattr(self.data.High, "s") else pd.Series(self.data.High)
        lo = self.data.Low.s if hasattr(self.data.Low, "s") else pd.Series(self.data.Low)
        s50 = sma(c, self.sma_fast)
        s200 = sma(c, self.sma_slow)
        _, _, hist = macd(c, self.macd_fast, self.macd_slow, self.macd_signal)
        atr_ser = atr(h, lo, c, self.atr_period)
        self.sma50 = self.I(lambda: s50, name="SMA50")
        self.sma200 = self.I(lambda: s200, name="SMA200")
        self.macd_hist = self.I(lambda: hist, name="MACD Hist")
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

    def _sma50_slope_positive(self) -> bool:
        if len(self.sma50) < 2:
            return False
        return self.sma50[-1] > self.sma50[-2]

    def next(self) -> None:
        i = len(self.data.Close) - 1
        close = self.data.Close[-1]
        s50 = self.sma50[-1]
        s200 = self.sma200[-1]
        hist = self.macd_hist[-1]
        atr_val = self.atr_ind[-1]

        if any(pd.isna(x) for x in [close, s50, s200, hist]):
            return

        if self.position:
            if close < s50 or hist < 0:
                self.position.close()
                self._record_close(i)
            return

        regime_ok = close > s200
        macd_ok = hist > 0
        slope_ok = self._sma50_slope_positive()
        buy_signal = regime_ok and s50 > s200 and macd_ok and slope_ok
        if not buy_signal or not self._can_open(i):
            return

        self._record_entry(i)
        sl = close - self.atr_mult_sl * atr_val if not pd.isna(atr_val) and atr_val > 0 else None
        self.buy(sl=sl)
