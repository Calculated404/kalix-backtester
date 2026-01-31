# Kalix Backtester

EUR/CHF backtesting system with **Mean Reversion** (Bollinger + RSI) and **Trend Following** (SMA + MACD) strategies. Built to iterate on strategy logic and to support a future **AI trader** that fetches data every 1 hour and reports buy/hold/sell via `/api/report`.

## Features

- **Data**: EUR/CHF from Yahoo Finance (`EURCHF=X`), daily candles; cached in `./data_cache/` by (ticker, interval, period). Data is preloaded on first request (or on Flask startup).
- **Constraints**: One open trade at a time; max new entries per ISO week (default 2, cap 4); cooldown after close (default 2 trading days).
- **Strategies**: Mean Reversion, Trend Following; select one or both in the UI.
- **Report API**: `POST /api/report` with `{ "strategy": "mean_reversion", "data": [ ...OHLCV bars ] }` returns `{ "signal": "buy"|"hold"|"sell", "signal_strength", "snapshot" }`. The backtester uses the same logic bar-by-bar; later this can be replaced by an AI model for real-time 1h decisions.
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
   ```

## Web UI

- **Chart**: Dynamic EUR/CHF candlestick chart for the selected period (1–5 years). Green dots = buy, red dots = sell after a backtest run.
- **Form**: Initial cash (amount to trade), period (1–5 years), strategy selection (Mean Reversion, Trend Following, or both), commission, max entries per week, cooldown days.
- **Results**: After **Run backtest**, metrics (win rate, total return %, max drawdown, # trades, avg trades/week, profit factor, expectancy) and run path. Trades and metrics are also saved under `./runs/<timestamp>_<strategy>_<period>/` (config.json, metrics.json, trades.csv, stats.json).

## Report flow (for AI trader)

The backtester simulates bar-by-bar using the same logic as `POST /api/report`. For a future **real-time AI trader**:

1. Every 1 hour, fetch current EUR/CHF data (e.g. last N bars).
2. Call `POST /api/report` with `{ "strategy": "mean_reversion" | "trend_following", "data": [ ...OHLCV ] }`.
3. Use the returned `signal` (buy/hold/sell) and optional `signal_strength` to place or hold positions; record P/L.

No live trading or broker APIs are implemented yet; only backtesting and the report API.

## Commission

Default commission is `0.00005` (0.005%) as a simple stand-in for spread and fees. This is a simplification and will be refined (e.g. per-broker, spread model) later.

## License

Internal use.
