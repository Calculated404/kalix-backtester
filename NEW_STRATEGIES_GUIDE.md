# New Strategy Implementations

## Overview

Two new trading strategies have been added to the Kalix Backtester:

1. **Double RSI** - Dual-timeframe RSI strategy for trend confirmation and timing
2. **TMV (Trend + Momentum + Volume)** - Multi-factor strategy combining trend, momentum, and volume analysis

Both strategies are now available in the backtester UI and API alongside the existing Mean Reversion and Trend Following strategies.

---

## 1. Double RSI Strategy

### Concept

The Double RSI strategy uses two RSI indicators with different periods to separate trend identification from entry timing:

- **Trend RSI** (longer period): Determines market bias (bullish/bearish/neutral)
- **Signal RSI** (shorter period): Generates precise entry/exit signals via crossovers

This approach helps avoid whipsaws by only taking signals aligned with the broader trend.

### Original Implementation (Sentinel)

The original implementation in `kalix_sentinel/indicators/double_rsi.py` used:
- **Daily RSI (7-period)** for trend bias
- **1-hour RSI (7-period)** for signal generation
- Cross-back triggers at 40/60 levels

### Backtester Adaptation

Since the backtester works with a single timeframe, we simulate dual-timeframe behavior using different RSI periods:

```python
trend_rsi_period = 21   # Simulates daily/higher timeframe
signal_rsi_period = 7   # Simulates hourly/signal timeframe
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `trend_rsi_period` | 21 | Longer period for trend bias |
| `signal_rsi_period` | 7 | Shorter period for entry signals |
| `trend_hi` | 60.0 | Bullish bias threshold |
| `trend_lo` | 40.0 | Bearish bias threshold |
| `buy_level` | 40.0 | Signal RSI cross-above level |
| `sell_level` | 60.0 | Signal RSI cross-below level |
| `atr_mult_sl` | 2.0 | Stop loss multiplier (ATR-based) |
| `atr_mult_tp` | 3.0 | Take profit multiplier (ATR-based) |
| `max_entries_per_week` | 2 | Maximum trades per week |
| `cooldown_days` | 1 | Days to wait after closing position |

### Entry Logic

**Long Entry** (only bullish trades implemented):
1. Trend RSI > 60 (bullish bias)
2. Signal RSI crosses above 40 (oversold bounce)
3. Position management constraints satisfied

**Exit Conditions**:
1. Trend bias changes to bearish or neutral
2. Signal RSI crosses below 60 (overbought)
3. Stop loss or take profit hit

### Indicator Calculation

Uses **Wilder's smoothing method** for RSI calculation:
```python
alpha = 1/period
avg_gain = EMA(gains, alpha)
avg_loss = EMA(losses, alpha)
RSI = 100 - (100 / (1 + avg_gain/avg_loss))
```

---

## 2. TMV Strategy (Trend + Momentum + Volume)

### Concept

The TMV strategy combines three independent confirmation factors:

1. **Trend**: Smoothed Heikin Ashi candles (green = bullish, red = bearish)
2. **Momentum**: Range Filter indicator (buy/sell flips)
3. **Volume**: Current volume > average volume

All three must align for trade entry (AND logic).

### Original Implementation (Sentinel)

The original implementation in `kalix_sentinel/indicators/tmv.py` used full OHLCV data to calculate:
- Smoothed Heikin Ashi with double EMA smoothing
- Range Filter with adaptive range calculation
- Volume confirmation vs 30-period SMA

### Backtester Adaptation

The backtester implementation faithfully reproduces the original logic using pandas-based indicators:

```python
# Trend component
sha_open, sha_close = smoothed_heikin_ashi(
    open, high, low, close,
    ma_period=50,
    smoothing=10
)

# Momentum component
rf_line, rf_upward, rf_downward = range_filter(
    high, low, close,
    period=100,
    multiplier=3.0
)

# Volume component
volume_sma = sma(volume, 30)
volume_confirmed = current_volume > volume_sma
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ha_period` | 50 | Heikin Ashi EMA period (first smoothing) |
| `ha_smoothing` | 10 | Heikin Ashi second smoothing period |
| `range_period` | 100 | Range Filter calculation period |
| `range_multiplier` | 3.0 | Range Filter sensitivity multiplier |
| `volume_sma` | 30 | Volume moving average period |
| `atr_mult_sl` | 2.0 | Stop loss multiplier (ATR-based) |
| `atr_mult_tp` | 3.0 | Take profit multiplier (ATR-based) |
| `max_entries_per_week` | 2 | Maximum trades per week |
| `cooldown_days` | 1 | Days to wait after closing position |

### Entry Logic

**Long Entry**:
1. **Trend**: Smoothed HA Close > Open (green candle, bullish)
2. **Momentum**: Range Filter generates BUY signal (crosses into long regime)
3. **Volume**: Current volume > 30-period SMA
4. Position management constraints satisfied

**Exit Conditions**:
1. Trend turns bearish (HA Close < Open)
2. Range Filter flips to SELL signal
3. Stop loss or take profit hit

### Component Details

#### Smoothed Heikin Ashi
1. First smoothing: Apply EMA(50) to raw OHLC
2. Calculate standard Heikin Ashi on smoothed data
3. Second smoothing: Apply EMA(10) to HA Open/Close

#### Range Filter
Based on the classic TradingView "Range Filter Buy & Sell" indicator:
1. Calculate smoothed range using double EMA
2. Create adaptive filter line based on price and range
3. Track upward/downward momentum counters
4. Generate buy/sell signals on regime transitions

#### Volume Confirmation
Simple but effective: only take signals when participation is above average, reducing false breakouts.

---

## New Indicator Functions

The following functions were added to `backend/strategies/indicators.py`:

### Double RSI Helpers

```python
def double_rsi(close: pd.Series, period: int = 7) -> pd.Series
```
Calculates RSI using Wilder's smoothing method (alpha = 1/period).

### TMV Helpers

```python
def ema(series: pd.Series, period: int) -> pd.Series
```
Exponential moving average.

```python
def heikin_ashi(open_, high, low, close) -> tuple[pd.Series, ...]
```
Standard Heikin Ashi candle calculation.

```python
def smoothed_heikin_ashi(open_, high, low, close, ma_period, smoothing) -> tuple[pd.Series, pd.Series]
```
Double-smoothed Heikin Ashi (returns open and close only).

```python
def range_filter(high, low, close, period, multiplier) -> tuple[pd.Series, pd.Series, pd.Series]
```
Range Filter indicator (returns filter line, upward counter, downward counter).

---

## Testing the New Strategies

### Via API

```bash
curl -X POST http://localhost:5003/api/run \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "EURCHF=X",
    "interval": "1d",
    "period_years": 5,
    "strategies": ["double_rsi", "tmv"],
    "initial_cash": 10000,
    "commission": 0.00005
  }'
```

### Via Frontend

1. Start the backtester: `cd kalix-backtester && python run_app.py`
2. Open the UI at http://localhost:5003
3. Select "double_rsi" or "tmv" from the Strategy/signals checkboxes
4. Configure parameters and click "Run backtest"

### Via Python

```python
from backend.strategies import get_strategy_class, list_strategies
from backend.data.loader import load_eurchf_data
from backtesting import Backtest

# Verify strategies are registered
print(list_strategies())  
# Output: ['double_rsi', 'mean_reversion', 'tmv', 'trend_following']

# Load data
df = load_eurchf_data(period_years=5)

# Run Double RSI backtest
DoubleRSIStrategy = get_strategy_class('double_rsi')
bt = Backtest(df, DoubleRSIStrategy, cash=10000, commission=0.00005)
stats = bt.run()
print(stats)

# Run TMV backtest
TMVStrategy = get_strategy_class('tmv')
bt = Backtest(df, TMVStrategy, cash=10000, commission=0.00005)
stats = bt.run()
print(stats)
```

---

## Strategy Registration

Both strategies are automatically registered using the `@register` decorator:

```python
from backend.strategies.base import register

@register("double_rsi")
class DoubleRSIStrategy(Strategy):
    ...

@register("tmv")
class TMVStrategy(Strategy):
    ...
```

This makes them instantly available via:
- `GET /api/strategies` endpoint
- `list_strategies()` function
- Frontend strategy selector

---

## Files Modified/Created

### Created
- `backend/strategies/double_rsi_strategy.py` - Double RSI strategy implementation
- `backend/strategies/tmv_strategy.py` - TMV strategy implementation

### Modified
- `backend/strategies/indicators.py` - Added indicator functions for both strategies
- `backend/strategies/__init__.py` - Export new strategy classes

### No Changes Needed
- `backend/app.py` - Uses dynamic strategy registry
- `frontend/src/components/BacktestForm.jsx` - Fetches strategies from API
- API schemas and endpoints - Work with any registered strategy

---

## Performance Considerations

### Double RSI
- **Pros**: Simple, fewer indicators, fast execution
- **Cons**: Single timeframe approximation may not fully capture dual-TF behavior
- **Best for**: Daily/hourly data where trend RSI period can meaningfully differ

### TMV
- **Pros**: Multi-factor confirmation reduces false signals
- **Cons**: More complex, slower due to multiple indicator calculations
- **Best for**: Markets with clear trends and volume data (stocks, major forex pairs)

Both strategies include:
- ATR-based stop loss and take profit
- Weekly trade limits
- Cooldown periods between trades
- Proper handling of NaN values and edge cases

---

## Future Enhancements

Potential improvements for consideration:

1. **Multi-timeframe data support**: Enable true dual-timeframe RSI in backtester
2. **Short selling**: Add bearish trade logic for Double RSI
3. **Parameter optimization**: Auto-tune parameters via grid search
4. **Strategy combinations**: Ensemble signals from multiple strategies
5. **Advanced exits**: Trailing stops, partial position closes
6. **Risk sizing**: Kelly criterion or volatility-based position sizing

---

## Conclusion

The Double RSI and TMV strategies are now fully integrated into the Kalix Backtester. They maintain fidelity to the original Sentinel indicator implementations while adapting to the backtester's pandas-based architecture.

Both strategies are production-ready and can be backtested on any supported ticker and timeframe alongside the existing strategies.
