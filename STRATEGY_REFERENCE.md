# Kalix Backtester - Strategy Reference

## Available Strategies

### 1. Trend + Momentum + Volume (TMV) ⭐ DEFAULT
**Strategy ID**: `trend_momentum_volume`

**Rules**: Smoothed Heikin Ashi (Period=50, Smoothing=10) + Range Filter (Period=100, Multiplier=3.0) + Volume SMA(30)

**Entry LONG**: 
- Trend is BULLISH (Smoothed HA Close > Open = Green candles)
- AND Range Filter triggers BUY signal or holds LONG regime  
- AND Current Volume > VolSMA(30) *[Auto-passes if volume data unavailable, e.g., Forex]*

**Entry SHORT**:
- Trend is BEARISH (Smoothed HA Close < Open = Red candles)
- AND Range Filter triggers SELL signal or holds SHORT regime
- AND Current Volume > VolSMA(30) *[Auto-passes if volume data unavailable, e.g., Forex]*

**Exit**:
- Trend reverses (LONG→BEARISH or SHORT→BULLISH)
- OR Range Filter flips to opposite signal
- OR Stop Loss / Take Profit hit (**ALWAYS 2:1 Risk/Reward**)

**Best for**: Strong trending markets with clear momentum breakouts in BOTH directions. Ideal timeframe: **1 Hour (H1)**.

**Components**:
- **Trend Filter**: Smoothed Heikin Ashi eliminates noise, shows pure trend direction
- **Momentum Signal**: Range Filter detects breakouts above/below dynamic support/resistance
- **Volume Confirmation**: 🔴 **CRITICAL FILTER** 🔴 - Ensures sufficient market participation (optional for Forex)

**Parameters**:
- `ha_period = 50` - First smoothing for Heikin Ashi
- `ha_smoothing = 10` - Second smoothing
- `range_period = 100` - Range Filter calculation period
- `range_multiplier = 3.0` - Range Filter sensitivity
- `volume_sma = 30` - Volume average period
- `atr_mult_sl = 2.0` - Stop loss (ATR multiplier)
- `atr_mult_tp = 4.0` - Take profit (ATR multiplier) - **2:1 ratio**
- `max_entries_per_week = 3`
- `cooldown_days = 0`

**Risk Management**: **ALWAYS 2:1 Reward-to-Risk Ratio**
- Stop Loss: Entry ± 2.0 × ATR
- Take Profit: Entry ± 4.0 × ATR
- Break-even win rate: 33.3% (only need 1 win per 2 losses!)

---

### 2. Mean Reversion
**Strategy ID**: `mean_reversion`

**Rules**: Bollinger Bands (period=20, std=2.0) + RSI (period=14, threshold=30) regime filter

**Entry**: 
- Price ≤ Lower Bollinger Band 
- AND RSI < 30 (oversold)

**Exit**: 
- Price ≥ Middle Bollinger Band (mean reversion complete)
- OR RSI > 50 (momentum returns)

**Best for**: Range-bound markets, sideways price action, mean-reverting instruments.

**Parameters**:
- `bb_window = 20`, `bb_std = 2.0`
- `rsi_period = 14`, `rsi_low = 30`, `rsi_exit = 50`
- `atr_mult_sl = 1.0`
- `max_entries_per_week = 2`
- `cooldown_days = 2`

---

### 3. Trend Following
**Strategy ID**: `trend_following`

**Rules**: SMA Crossover (50/200) + MACD confirmation

**Entry**: 
- Close > SMA200 (long-term uptrend)
- AND SMA50 > SMA200 (golden cross active)
- AND MACD histogram > 0 (momentum positive)
- AND SMA50 slope positive (trend accelerating)

**Exit**: 
- Close < SMA50 (trend breaks)
- OR MACD histogram < 0 (momentum fades)

**Best for**: Strong, sustained trending markets with clear directional bias.

**Parameters**:
- `sma_fast = 50`, `sma_slow = 200`
- `macd_fast = 12`, `macd_slow = 26`, `macd_signal = 9`
- `atr_mult_sl = 1.0`
- `max_entries_per_week = 2`
- `cooldown_days = 2`

---

### 4. Double RSI
**Strategy ID**: `double_rsi`

**Rules**: Dual-timeframe RSI - Trend RSI(21) for bias + Signal RSI(7) for timing

**Entry**: 
- Trend RSI > 60 (BULLISH bias established)
- AND Signal RSI crosses above 40 (oversold bounce on shorter timeframe)

**Exit**: 
- Trend RSI < 40 (bias lost / NEUTRAL or BEARISH)
- OR Signal RSI crosses below 60 (overbought, take profits)
- OR Stop Loss/Take Profit hit

**Best for**: Markets with clear trends punctuated by short-term pullbacks/mean reversion.

**Parameters**:
- `trend_rsi_period = 21` (longer period = trend bias)
- `signal_rsi_period = 7` (shorter period = entry timing)
- `trend_hi = 60`, `trend_lo = 40` (bias thresholds)
- `buy_level = 40`, `sell_level = 60` (entry/exit levels)
- `atr_mult_sl = 2.0`, `atr_mult_tp = 3.0`
- `max_entries_per_week = 2`
- `cooldown_days = 1`

---

## Strategy Comparison

| Strategy | Type | Timeframe | Win Rate¹ | Complexity | Volume Required |
|----------|------|-----------|-----------|------------|-----------------|
| **TMV** | Trend/Momentum | 1H (preferred) | Variable | High | Optional² |
| **Mean Reversion** | Counter-trend | 1D | Medium-High | Low | No |
| **Trend Following** | Trend | 1D | Low-Medium | Medium | No |
| **Double RSI** | Trend + Timing | 1H-1D | Medium | Medium | No |

¹ Win rate varies by market and parameters  
² Volume confirmation skipped if data unavailable (e.g., Forex pairs)

---

## Timeframe Recommendations

### 1 Hour (1H) ⭐ Recommended for TMV
- **Best**: TMV (designed for 1H), Double RSI
- **Good**: Mean Reversion (more signals)
- **Okay**: Trend Following (needs longer data)

### 4 Hour (4H)
- **Best**: Trend Following, TMV
- **Good**: Double RSI
- **Okay**: Mean Reversion (fewer signals)

### 1 Day (1D)
- **Best**: Trend Following, Mean Reversion
- **Good**: Double RSI
- **Okay**: TMV (fewer signals, slower)

---

## Default Settings

When you open the backtester:
- **Default Strategy**: Trend + Momentum + Volume (TMV)
- **Default Timeframe**: 1 Hour (1H)
- **Default Symbol**: EUR/CHF
- **Default Period**: 2 years (max for hourly data)
- **Default Capital**: $10,000
- **Default Commission**: 0.00005 (0.005%)

You can change any of these settings before running a backtest.

---

## Volume Data Handling

### Forex Pairs (EUR/CHF, GBP/USD, etc.)
Yahoo Finance does not provide volume data for Forex pairs (all volumes = 0). The TMV strategy automatically **disables volume confirmation** when volume data is unavailable, relying only on Trend + Momentum factors.

### Stocks & ETFs (NVDA, AAPL, SPY, etc.)
Full volume data available. TMV uses volume confirmation as designed: current volume must exceed 30-period average.

### Commodities (Gold, Silver, etc.)
Volume data available for futures contracts. Volume confirmation active.

---

## Risk Management (All Strategies)

All strategies use **ATR-based** (Average True Range) stops and targets:

- **Stop Loss**: Adaptive to volatility, prevents catastrophic losses
- **Take Profit**: Risk/Reward optimized (typically 2-3x ATR)
- **Position Sizing**: Fixed fraction of capital (managed by backtester)
- **Max Entries**: Weekly limits prevent overtrading
- **Cooldown**: Optional delay between trades (varies by strategy)

---

## TradingView Indicators (For Chart Analysis)

To visualize TMV components on TradingView, add these indicators:

1. **Range Filter Buy & Sell 5min**
   - Search: "Range Filter Buy and Sell"
   - Settings: Period = 100, Multiplier = 3.0
   - Shows: Support/Resistance bands + Buy/Sell signals

2. **Market Bias (CEREBR)**
   - Search: "Market Bias CEREBR" or "Smoothed Heikin Ashi"
   - Settings: Period = 50, Smoothing = 10
   - Shows: Green/Red candles for trend direction

3. **Volume SMA**
   - Built-in: Add Volume indicator
   - Settings: Add SMA(30) overlay
   - Shows: Volume confirmation threshold

Note: These are for visualization only. The backtester calculates all indicators internally.

---

## Strategy Selection Tips

1. **Not sure which strategy?** Start with **TMV** on **1H timeframe** - it's the most versatile.

2. **Range-bound market?** Use **Mean Reversion** on **1D timeframe**.

3. **Strong trend?** Use **Trend Following** on **4H or 1D**.

4. **Testing multiple strategies?** Check all boxes and compare results side-by-side.

5. **Optimize parameters?** Each strategy exposes tunable parameters - experiment!

---

## Next Steps

- Run backtests on different symbols (Forex, Stocks, Commodities)
- Compare strategies side-by-side
- Experiment with different timeframes
- Adjust parameters for your trading style
- Export results for further analysis

For detailed implementation notes, see:
- `NEW_STRATEGIES_GUIDE.md` - In-depth strategy documentation
- `IMPLEMENTATION_SUMMARY.md` - Technical implementation details
