"""Double RSI Strategy: Uses dual-timeframe RSI for trend bias and signals."""
from __future__ import annotations

import pandas as pd
from backtesting import Strategy

from backend.strategies.base import register
from backend.strategies.indicators import atr, double_rsi


@register("double_rsi")
class DoubleRSIStrategy(Strategy):
    """Double RSI Strategy.
    
    Rules: Dual-timeframe RSI - Trend RSI(21) for bias + Signal RSI(7) for timing
    
    Entry: Trend RSI > 60 (BULLISH bias) AND Signal RSI crosses above 40 (oversold bounce)
    
    Exit: Trend RSI < 40 (bias lost) OR Signal RSI crosses below 60 (overbought) OR Stop Loss/Take Profit hit
    
    Uses a trend RSI (longer period) to determine bias and a signal RSI (shorter period)
    for precise entry/exit timing via crossovers.
    """
    
    # RSI parameters - OPTIMIZED for more signals
    trend_rsi_period = 14  # Reduced from 21 for faster trend detection
    signal_rsi_period = 7  # Keep at 7 for signal timing
    
    # Thresholds - RELAXED for more trades
    trend_hi = 55.0  # Reduced from 60 (easier to reach bullish)
    trend_lo = 45.0  # Increased from 40 (easier to reach bearish)
    buy_level = 35.0  # Reduced from 40 (more buy opportunities)
    sell_level = 65.0  # Increased from 60 (more sell opportunities)
    
    # Risk management - 2:1 ratio
    atr_period = 14
    atr_mult_sl = 1.5  # Tighter stop
    atr_mult_tp = 3.0  # 2:1 ratio (3.0 / 1.5)
    
    # Position management - MORE TRADES
    max_entries_per_week = 3  # Increased from 2
    cooldown_days = 0  # Removed cooldown
    
    def init(self) -> None:
        import pandas as pd
        c = self.data.Close.s if hasattr(self.data.Close, "s") else pd.Series(self.data.Close)
        h = self.data.High.s if hasattr(self.data.High, "s") else pd.Series(self.data.High)
        lo = self.data.Low.s if hasattr(self.data.Low, "s") else pd.Series(self.data.Low)
        
        # Calculate trend and signal RSI
        trend_rsi_ser = double_rsi(c, self.trend_rsi_period)
        signal_rsi_ser = double_rsi(c, self.signal_rsi_period)
        
        # ATR for stops
        atr_ser = atr(h, lo, c, self.atr_period)
        
        self.trend_rsi = self.I(lambda: trend_rsi_ser, name="Trend RSI")
        self.signal_rsi = self.I(lambda: signal_rsi_ser, name="Signal RSI")
        self.atr_ind = self.I(lambda: atr_ser, name="ATR")
        
        self._entries_this_week: dict[str, int] = {}
        self._last_close_bar: int | None = None
        self._last_trend_bias: str | None = None
    
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
    
    def _get_trend_bias(self) -> str:
        """Determine trend bias from trend RSI."""
        trend_rsi_val = self.trend_rsi[-1]
        if pd.isna(trend_rsi_val):
            return "UNKNOWN"
        if trend_rsi_val > self.trend_hi:
            return "BULLISH"
        elif trend_rsi_val < self.trend_lo:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def next(self) -> None:
        i = len(self.data.Close) - 1
        close = self.data.Close[-1]
        trend_rsi_val = self.trend_rsi[-1]
        signal_rsi_val = self.signal_rsi[-1]
        atr_val = self.atr_ind[-1]
        
        # Need at least 2 signal RSI values to detect crosses
        if len(self.signal_rsi) < 2:
            return
        
        prev_signal_rsi = self.signal_rsi[-2]
        
        if any(pd.isna(x) for x in [close, trend_rsi_val, signal_rsi_val, prev_signal_rsi]):
            return
        
        trend_bias = self._get_trend_bias()
        
        # Exit logic
        if self.position:
            if self.position.is_long:
                # Exit LONG: bias lost or signal RSI overbought
                if trend_bias in ("BEARISH", "NEUTRAL"):
                    self.position.close()
                    self._record_close(i)
                    return
                elif prev_signal_rsi <= self.sell_level < signal_rsi_val:
                    self.position.close()
                    self._record_close(i)
                    return
            elif self.position.is_short:
                # Exit SHORT: bias lost or signal RSI oversold
                if trend_bias in ("BULLISH", "NEUTRAL"):
                    self.position.close()
                    self._record_close(i)
                    return
                elif prev_signal_rsi >= self.buy_level > signal_rsi_val:
                    self.position.close()
                    self._record_close(i)
                    return
        
        # Entry logic - BOTH LONG AND SHORT
        if not self.position:
            # LONG Entry: Bullish bias + signal RSI crosses above buy level
            if trend_bias == "BULLISH":
                if prev_signal_rsi <= self.buy_level < signal_rsi_val:
                    if self._can_open(i):
                        self._record_entry(i)
                        self._last_trend_bias = "BULLISH"
                        
                        sl = close - self.atr_mult_sl * atr_val if not pd.isna(atr_val) and atr_val > 0 else None
                        tp = close + self.atr_mult_tp * atr_val if not pd.isna(atr_val) and atr_val > 0 else None
                        self.buy(sl=sl, tp=tp)
            
            # SHORT Entry: Bearish bias + signal RSI crosses below sell level
            elif trend_bias == "BEARISH":
                if prev_signal_rsi >= self.sell_level > signal_rsi_val:
                    if self._can_open(i):
                        self._record_entry(i)
                        self._last_trend_bias = "BEARISH"
                        
                        sl = close + self.atr_mult_sl * atr_val if not pd.isna(atr_val) and atr_val > 0 else None
                        tp = close - self.atr_mult_tp * atr_val if not pd.isna(atr_val) and atr_val > 0 else None
                        self.sell(sl=sl, tp=tp)
