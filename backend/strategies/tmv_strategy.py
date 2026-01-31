"""TMV Strategy: Trend + Momentum + Volume confirmation."""
from __future__ import annotations

import pandas as pd
from backtesting import Strategy

from backend.strategies.base import register
from backend.strategies.indicators import atr, ema, range_filter, sma, smoothed_heikin_ashi


@register("trend_momentum_volume")
class TMVStrategy(Strategy):
    """Trend + Momentum + Volume (TMV) Strategy - OPTIMIZED for 1H timeframe.
    
    Rules: Smoothed Heikin Ashi (Period=30, Smoothing=5) + Range Filter (Period=50, Multiplier=2.5) + Volume SMA(20)
    
    Entry LONG: Trend is BULLISH (Green HA) AND Range Filter BUY signal (transition) AND Current Volume > VolSMA(20)
    
    Entry SHORT: Trend is BEARISH (Red HA) AND Range Filter SELL signal (transition) AND Current Volume > VolSMA(20)
    
    Exit: Trend reverses OR Range Filter flips OR 2:1 Risk/Reward Stop Loss/Take Profit hit
    
    Risk Management: ALWAYS 2:1 Reward-to-Risk Ratio (Stop: 1.5xATR, Target: 3.0xATR)
    
    OPTIMIZATIONS:
    - Faster trend detection (HA 30/5 vs 50/10)
    - More frequent signals (Range Filter 50 vs 100)
    - Tighter risk management (1.5 ATR stop vs 2.0)
    - More selective entries (only on signal transitions)
    - Quality over quantity (max 2 trades/week + 1-day cooldown)
    
    Components:
    - Trend: Smoothed Heikin Ashi bias (green=bullish, red=bearish)
    - Momentum: Range Filter buy/sell breakout signals
    - Volume: Current volume > 20-period SMA (participation confirmation)
    """
    
    # Heikin Ashi parameters - OPTIMIZED for better trend detection
    ha_period = 30  # Reduced from 50 for faster trend detection
    ha_smoothing = 5  # Reduced from 10 for more responsiveness
    
    # Range Filter parameters - OPTIMIZED for clearer signals
    range_period = 50  # Reduced from 100 for more frequent signals
    range_multiplier = 2.5  # Reduced from 3.0 for tighter bands (more signals)
    
    # Volume parameters
    volume_sma = 20  # Reduced from 30 for more responsive volume detection
    
    # Risk management - ALWAYS 2:1 Reward-to-Risk Ratio
    atr_period = 14
    atr_mult_sl = 1.5  # Tighter stop: 1.5 x ATR (was 2.0)
    atr_mult_tp = 3.0  # Still 2:1 ratio: 3.0 / 1.5 = 2:1
    
    # Position management - MORE SELECTIVE
    max_entries_per_week = 2  # Reduced from 3 for quality over quantity
    cooldown_days = 1  # Added 1-day cooldown to avoid overtrading
    
    def init(self) -> None:
        import pandas as pd
        
        # Get data series
        o = self.data.Open.s if hasattr(self.data.Open, "s") else pd.Series(self.data.Open)
        h = self.data.High.s if hasattr(self.data.High, "s") else pd.Series(self.data.High)
        l = self.data.Low.s if hasattr(self.data.Low, "s") else pd.Series(self.data.Low)
        c = self.data.Close.s if hasattr(self.data.Close, "s") else pd.Series(self.data.Close)
        v = self.data.Volume.s if hasattr(self.data.Volume, "s") else pd.Series(self.data.Volume)
        
        # Calculate Smoothed Heikin Ashi
        sha_open, sha_close = smoothed_heikin_ashi(o, h, l, c, self.ha_period, self.ha_smoothing)
        
        # Calculate Range Filter
        rf_line, rf_upward, rf_downward = range_filter(h, l, c, self.range_period, self.range_multiplier)
        
        # Calculate Volume SMA
        vol_sma = sma(v, self.volume_sma)
        
        # Calculate ATR for stops
        atr_ser = atr(h, l, c, self.atr_period)
        
        # Store indicators
        self.sha_open = self.I(lambda: sha_open, name="HA Open")
        self.sha_close = self.I(lambda: sha_close, name="HA Close")
        self.rf_line = self.I(lambda: rf_line, name="Range Filter")
        self.rf_upward = self.I(lambda: rf_upward, name="RF Upward")
        self.rf_downward = self.I(lambda: rf_downward, name="RF Downward")
        self.vol_sma = self.I(lambda: vol_sma, name="Volume SMA")
        self.atr_ind = self.I(lambda: atr_ser, name="ATR")
        
        self._entries_this_week: dict[str, int] = {}
        self._last_close_bar: int | None = None
        self._last_rf_state: int = 0  # Track Range Filter state
    
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
    
    def _get_ha_trend(self) -> str:
        """Get Heikin Ashi trend: BULLISH, BEARISH, or NEUTRAL."""
        sha_open_val = self.sha_open[-1]
        sha_close_val = self.sha_close[-1]
        
        if pd.isna(sha_open_val) or pd.isna(sha_close_val):
            return "NEUTRAL"
        
        if sha_close_val > sha_open_val:
            return "BULLISH"
        elif sha_close_val < sha_open_val:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def _get_range_filter_signal(self) -> tuple[str, int]:
        """Get Range Filter signal: buy, sell, or holding.
        
        Returns:
            (signal, state) where state is 1 for long regime, -1 for short, 0 for neutral
        """
        if len(self.rf_line) < 2:
            return "neutral", 0
        
        # Use Close as source (more standard for breakouts)
        src = self.data.Close[-1]
        src_prev = self.data.Close[-2]
        filt = self.rf_line[-1]
        filt_prev = self.rf_line[-2] if len(self.rf_line) >= 2 else filt
        upward = self.rf_upward[-1]
        downward = self.rf_downward[-1]
        
        if pd.isna(src) or pd.isna(filt) or pd.isna(upward) or pd.isna(downward):
            return "neutral", 0
        
        # More relaxed conditions: just need to be above/below filter with momentum
        long_cond = (src > filt) and (upward > 0)
        short_cond = (src < filt) and (downward > 0)
        
        # Update state based on current conditions
        current_state = self._last_rf_state
        if long_cond:
            current_state = 1
        elif short_cond:
            current_state = -1
        
        # Detect FLIP transitions (more aggressive entry detection)
        # Buy: was in short/neutral regime and now in long regime
        # OR: price crosses above filter line (breakout)
        buy_signal = False
        if self._last_rf_state <= 0 and current_state == 1:
            buy_signal = True
        elif src_prev <= filt_prev and src > filt and upward > 0:
            buy_signal = True
        
        # Sell: was in long/neutral regime and now in short regime
        # OR: price crosses below filter line (breakdown)
        sell_signal = False
        if self._last_rf_state >= 0 and current_state == -1:
            sell_signal = True
        elif src_prev >= filt_prev and src < filt and downward > 0:
            sell_signal = True
        
        # Update stored state
        self._last_rf_state = current_state
        
        if buy_signal:
            return "buy", current_state
        elif sell_signal:
            return "sell", current_state
        elif current_state == 1:
            return "hold_long", current_state
        elif current_state == -1:
            return "hold_short", current_state
        else:
            return "neutral", current_state
    
    def _get_volume_confirmation(self) -> bool:
        """Check if current volume > average volume.
        
        NOW ENFORCED: Volume filter is ALWAYS active (using synthetic volume for Forex if needed).
        """
        current_vol = self.data.Volume[-1]
        avg_vol = self.vol_sma[-1]
        
        if pd.isna(current_vol) or pd.isna(avg_vol):
            return False  # No volume data = no trade
        
        # If average is very low but current exists, check ratio
        if avg_vol < 100:
            return False  # Suspicious data, skip
        
        return current_vol > avg_vol
    
    def next(self) -> None:
        i = len(self.data.Close) - 1
        close = self.data.Close[-1]
        atr_val = self.atr_ind[-1]
        
        # Get all three components
        ha_trend = self._get_ha_trend()
        rf_signal, rf_state = self._get_range_filter_signal()
        volume_confirmed = self._get_volume_confirmation()
        
        # Exit logic - Close position if conditions reverse
        if self.position:
            if self.position.is_long:
                # Exit LONG if trend turns bearish OR Range Filter flips to sell
                if ha_trend == "BEARISH" or rf_signal == "sell":
                    self.position.close()
                    self._record_close(i)
                    return
            elif self.position.is_short:
                # Exit SHORT if trend turns bullish OR Range Filter flips to buy
                if ha_trend == "BULLISH" or rf_signal == "buy":
                    self.position.close()
                    self._record_close(i)
                    return
        
        # Entry logic: All three components must align (Trend + Momentum + Volume)
        # MORE SELECTIVE: Only enter on actual BUY/SELL signals, not on hold states
        if not self.position:
            # LONG ENTRY: Bullish HA + Range Filter BUY signal (transition) + Volume confirmation
            if ha_trend == "BULLISH" and volume_confirmed:
                if rf_signal == "buy":  # Only enter on actual buy signal, not hold_long
                    if self._can_open(i):
                        self._record_entry(i)
                        
                        # Calculate 2:1 Risk/Reward
                        sl = close - self.atr_mult_sl * atr_val if not pd.isna(atr_val) and atr_val > 0 else None
                        tp = close + self.atr_mult_tp * atr_val if not pd.isna(atr_val) and atr_val > 0 else None
                        
                        self.buy(sl=sl, tp=tp)
            
            # SHORT ENTRY: Bearish HA + Range Filter SELL signal (transition) + Volume confirmation
            elif ha_trend == "BEARISH" and volume_confirmed:
                if rf_signal == "sell":  # Only enter on actual sell signal, not hold_short
                    if self._can_open(i):
                        self._record_entry(i)
                        
                        # Calculate 2:1 Risk/Reward for SHORT
                        sl = close + self.atr_mult_sl * atr_val if not pd.isna(atr_val) and atr_val > 0 else None
                        tp = close - self.atr_mult_tp * atr_val if not pd.isna(atr_val) and atr_val > 0 else None
                        
                        self.sell(sl=sl, tp=tp)
