# Kalix Backtester

Multi-symbol backtesting system with **four trading strategies**: Mean Reversion (Bollinger + RSI), Trend Following (SMA + MACD), Double RSI (dual-timeframe RSI), and TMV (Trend + Momentum + Volume). Built to iterate on strategy logic and to support a future **AI trader** that fetches data every 1 hour and reports buy/hold/sell via `/api/report`.

## Features

- **Data**: Multi-symbol support (Forex, Commodities, Stocks) from Yahoo Finance; cached in `./data_cache/` by (ticker, interval, period). Data is preloaded on first request (or on Flask startup).
- **Timeframes**: Multiple intervals supported - 1m, 15m, 1h, 4h, 1d (subject to Yahoo Finance historical data availability).
- **Constraints**: One open trade at a time; max new entries per ISO week (default 2, cap 4); cooldown after close (default 2 trading days).
- **Strategies**: 
  - **Mean Reversion**: Bollinger Bands + RSI bounce strategy
  - **Trend Following**: SMA crossover + MACD confirmation
  - **Double RSI**: Dual-timeframe RSI for trend bias and signal timing
  - **TMV**: Multi-factor strategy combining Smoothed Heikin Ashi (trend), Range Filter (momentum), and Volume confirmation
  - Select one or multiple strategies in the UI for comparison
- **Report API**: `POST /api/report` with `{ "strategy": "...", "data": [ ...OHLCV bars ] }` returns `{ "signal": "buy"|"hold"|"sell", "signal_strength", "snapshot" }`. The backtester uses the same logic bar-by-bar; later this can be replaced by an AI model for real-time 1h decisions.
- **Costs**: Configurable commission (default 0.00005) to approximate spread+fees; see README for caveats.

## Setup

### Backend (Python 3.11+)

```bash
cd kalix-backtester
python3 -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

## Run

1. **Start backend** (from project root, with venv active):

   ```bash
   python run_app.py
   ```
   Or: `python -m backend.app` (with `PYTHONPATH=.` or from project root after `pip install -e .`).

   Backend runs at `http://127.0.0.1:5001` (set `PORT=5000` if you prefer). It preloads EUR/CHF data for 5 years on startup.

2. **Start frontend** (from `frontend/`):

   ```bash
   npm run dev
   ```
   Open `http://localhost:3000`. The app proxies `/api` to the backend.

3. **CLI backtest** (no UI):

   ```bash
   python -m kalix_backtester.cli --strategy mean_reversion --years 5
   # Or use the new strategies:
   python -m kalix_backtester.cli --strategy double_rsi --years 5
   python -m kalix_backtester.cli --strategy tmv --years 5
   ```

## Available Strategies

### 1. Mean Reversion
- **Entry**: Close <= Lower Bollinger Band AND RSI < 30
- **Exit**: Close >= Middle Band OR RSI > 50
- **Best for**: Range-bound markets, mean reversion patterns
- **Key parameters**: BB window (20), RSI period (14), ATR stop (1x)

### 2. Trend Following
- **Entry**: Close > SMA200, SMA50 > SMA200, MACD histogram > 0, SMA50 rising
- **Exit**: Close < SMA50 OR MACD histogram < 0
- **Best for**: Strong trending markets
- **Key parameters**: SMA periods (50/200), MACD (12/26/9), ATR stop (1x)

### 3. Double RSI (New!)
- **Entry**: Trend RSI > 60 (bullish bias), Signal RSI crosses above 40
- **Exit**: Trend bias changes OR Signal RSI crosses below 60
- **Best for**: Markets with clear trends and mean reversion on shorter timeframes
- **Key parameters**: Trend RSI (21), Signal RSI (7), thresholds (40/60), ATR stop (2x)
- **Source**: Adapted from Sentinel `double_rsi` indicator

### 4. TMV - Trend + Momentum + Volume (New!)
- **Entry**: ALL three must align:
  - Smoothed Heikin Ashi bullish (green candle)
  - Range Filter buy signal
  - Volume > 30-period SMA
- **Exit**: Trend turns bearish OR Range Filter sell signal
- **Best for**: Markets with clear trends and volume data (stocks, major forex)
- **Key parameters**: HA periods (50/10), Range Filter (100 period, 3.0 multiplier), ATR stop (2x)
- **Source**: Adapted from Sentinel `tmv` indicator

For detailed strategy documentation, see:
- `NEW_STRATEGIES_GUIDE.md` - Comprehensive guide to Double RSI and TMV
- `IMPLEMENTATION_SUMMARY.md` - Implementation details and testing results

## Web UI

- **Chart**: Dynamic multi-symbol candlestick chart for the selected period (1–5 years) and timeframe (1m to 1d). Green dots = buy, red dots = sell after a backtest run.
- **Form**: 
  - Symbol selection (Forex pairs, commodities, stocks)
  - Timeframe selection (1m, 15m, 1h, 4h, 1d)
  - Initial cash (amount to trade)
  - Period (1–5 years, limited by timeframe data availability)
  - Strategy selection (Mean Reversion, Trend Following, Double RSI, TMV - select multiple for comparison)
  - Commission, max entries per week, cooldown days
- **Results**: After **Run backtest**, metrics (win rate, total return %, max drawdown, # trades, avg trades/week, profit factor, expectancy, Sharpe ratio) and run path. Trades and metrics are also saved under `./runs/<timestamp>_<strategy>_<period>/` (config.json, metrics.json, trades.csv, stats.json).

## Report flow (for AI trader)

The backtester simulates bar-by-bar using the same logic as `POST /api/report`. For a future **real-time AI trader**:

1. Every 1 hour, fetch current data for your chosen symbol (e.g. last N bars).
2. Call `POST /api/report` with `{ "strategy": "mean_reversion" | "trend_following" | "double_rsi" | "tmv", "data": [ ...OHLCV ] }`.
3. Use the returned `signal` (buy/hold/sell) and optional `signal_strength` to place or hold positions; record P/L.

No live trading or broker APIs are implemented yet; only backtesting and the report API.

### Example API Usage

```bash
# Get available strategies
curl http://localhost:5003/api/strategies

# Run backtest with multiple strategies
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

# Get real-time signal
curl -X POST http://localhost:5003/api/report \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "tmv",
    "data": [
      {"Open": 0.945, "High": 0.948, "Low": 0.943, "Close": 0.947, "Volume": 50000}
    ]
  }'
```

## Commission

Default commission is `0.00005` (0.005%) as a simple stand-in for spread and fees. This is a simplification and will be refined (e.g. per-broker, spread model) later.

## License

Internal use.
