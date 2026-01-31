"""
Flask app for kalix-backtester.
Preloads EUR/CHF data on startup; serves API for React frontend and /report for AI trader.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from backend.config import BacktestConfig
from backend.data.loader import load_eurchf_data
from backend.engine.backtester import run_backtest
from backend.engine.report import report_signal
from backend.strategies import list_strategies

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

app = Flask(__name__, static_folder=None)
CORS(app)

# Preloaded data: key = period_years, value = DataFrame (as dict of lists for JSON)
_DATA_CACHE: dict[int, list[dict]] = {}
_CACHE_DIR = os.environ.get("KALIX_DATA_CACHE", "data_cache")
_RUNS_DIR = os.environ.get("KALIX_RUNS_DIR", "runs")


def _ensure_data(period_years: int) -> list[dict]:
    """Get chart data for period; load and cache on first use."""
    if period_years not in _DATA_CACHE:
        df = load_eurchf_data(period_years=period_years, cache_dir=_CACHE_DIR)
        # Index as ISO string for JSON
        df = df.reset_index()
        df = df.rename(columns={df.columns[0]: "time"})
        df["time"] = df["time"].astype(str)
        _DATA_CACHE[period_years] = df.to_dict("records")
    return _DATA_CACHE[period_years]


@app.before_request
def _log_request():
    LOG.debug("%s %s", request.method, request.path)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/strategies")
def api_strategies():
    return jsonify({"strategies": list_strategies()})


@app.route("/api/data")
def api_data():
    """Return OHLCV chart data for selected period, ticker, and interval. Preloaded on first request."""
    period = request.args.get("period_years", type=int, default=5)
    if period not in (1, 2, 3, 4, 5):
        period = 5
    ticker = request.args.get("ticker", "EURCHF=X")
    interval = request.args.get("interval", "1d")

    # Create a cache key that includes ticker and interval
    cache_key = (period, ticker, interval)

    # Use a simple approach: store in a nested cache structure
    if not hasattr(app, '_data_cache_full'):
        app._data_cache_full = {}

    if cache_key not in app._data_cache_full:
        df = load_eurchf_data(ticker=ticker, interval=interval, period_years=period, cache_dir=_CACHE_DIR)

        # Ensure we have required columns
        if df.empty:
            return jsonify({"data": [], "period_years": period, "ticker": ticker, "interval": interval, "error": "No data available"}), 400

        # Properly handle the index (datetime)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        df_copy = df.copy()
        df_copy.index.name = "time"
        df_copy = df_copy.reset_index()

        # Ensure proper column names (case-sensitive for frontend)
        required_cols = ["time", "Open", "High", "Low", "Close", "Volume"]
        for col in required_cols:
            if col not in df_copy.columns:
                # Try to find with different case
                for existing_col in df_copy.columns:
                    if existing_col.lower() == col.lower():
                        df_copy = df_copy.rename(columns={existing_col: col})
                        break

        # Convert datetime to ISO string, preserving time for intraday data
        # For 1d: just date (YYYY-MM-DD)
        # For intraday (1m, 15m, 1h, 4h): full datetime (YYYY-MM-DD HH:MM:SS)
        if interval in ['1d', '1w', '1mo']:
            df_copy["time"] = pd.to_datetime(df_copy["time"]).dt.strftime("%Y-%m-%d")
        else:
            # For intraday, keep full datetime
            df_copy["time"] = pd.to_datetime(df_copy["time"]).dt.strftime("%Y-%m-%d %H:%M:%S")

        # Convert to list of dicts with only required columns
        data = df_copy[required_cols].to_dict("records")
        app._data_cache_full[cache_key] = data

        LOG.debug(f"Cached {len(data)} records for {ticker} {interval} {period}y")
    else:
        data = app._data_cache_full[cache_key]

    return jsonify({"data": data, "period_years": period, "ticker": ticker, "interval": interval})


@app.route("/api/report", methods=["POST"])
def api_report():
    """
    Report endpoint: given strategy name and chart data (or last N bars), return buy/hold/sell.
    Called every 1h by the AI trader with current data; backtester uses same logic bar-by-bar.
    """
    body = request.get_json() or {}
    strategy_name = body.get("strategy", "mean_reversion")
    # Accept either full OHLCV array or pre-aggregated snapshot
    data = body.get("data")
    if data is None:
        return jsonify({"signal": "hold", "signal_strength": 0.0, "snapshot": {}, "error": "Missing 'data'"}), 400
    import pandas as pd
    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame([data])
    if "Close" not in df.columns and "close" in df.columns:
        df["Close"] = df["close"]
    if "Open" not in df.columns:
        df["Open"] = df.get("Close", df.get("close", 0))
    if "High" not in df.columns:
        df["High"] = df["Close"]
    if "Low" not in df.columns:
        df["Low"] = df["Close"]
    if "Volume" not in df.columns:
        df["Volume"] = 0
    result = report_signal(strategy_name, df)
    return jsonify(result)


@app.route("/api/run", methods=["POST"])
def api_run():
    """Run backtest(s); return metrics, trades, run paths, and trade markers for chart."""
    body = request.get_json() or {}
    ticker = body.get("ticker", "EURCHF=X")
    interval = body.get("interval", "1d")
    period_years = int(body.get("period_years", 5))
    strategies = body.get("strategies", ["mean_reversion"])
    if isinstance(strategies, str):
        strategies = [strategies]
    initial_cash = float(body.get("initial_cash", 10_000))
    commission = float(body.get("commission", 0.00005))
    max_entries_per_week = min(4, max(1, int(body.get("max_entries_per_week", 2))))
    cooldown_days = max(0, int(body.get("cooldown_days", 2)))

    period_years = max(1, min(5, period_years))
    df = load_eurchf_data(ticker=ticker, interval=interval, period_years=period_years, cache_dir=_CACHE_DIR)

    config = BacktestConfig(
        ticker=ticker,
        interval=interval,
        period_years=period_years,
        strategies=strategies,
        initial_cash=initial_cash,
        commission=commission,
        max_entries_per_week=max_entries_per_week,
        cooldown_days=cooldown_days,
    )

    results = []
    for name in strategies:
        if name not in list_strategies():
            continue
        try:
            out = run_backtest(df.copy(), config, name, runs_dir=_RUNS_DIR)
            trades = out.get("trades", [])
            # Build chart markers: green = entry, red = exit
            markers = []
            for t in trades:
                et = t.get("entry_time")
                ex = t.get("exit_time")
                ep = t.get("entry_price")
                exp = t.get("exit_price")
                if et is not None and ep is not None:
                    markers.append({"time": str(et), "price": float(ep), "type": "buy"})
                if ex is not None and exp is not None:
                    markers.append({"time": str(ex), "price": float(exp), "type": "sell"})
            results.append({
                "strategy": name,
                "metrics": out.get("metrics", {}),
                "trades": trades,
                "markers": markers,
                "indicators": out.get("indicators", {}),
                "run_path": out.get("run_path", ""),
            })
        except Exception as e:
            LOG.exception("Backtest failed for %s", name)
            results.append({"strategy": name, "error": str(e), "metrics": {}, "trades": [], "markers": []})

    return jsonify({"results": results, "period_years": period_years})


@app.route("/api/runs/<path:filename>")
def serve_run_file(filename):
    """Serve a file from runs dir (e.g. trades.csv, metrics.json)."""
    return send_from_directory(_RUNS_DIR, filename)


def preload_data():
    """Preload EUR/CHF for 5 years on startup so first backtest is fast."""
    try:
        _ensure_data(5)
        LOG.info("Preloaded EUR/CHF data for 5 years")
    except Exception as e:
        LOG.warning("Preload failed (will load on first request): %s", e)


if __name__ == "__main__":
    preload_data()
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
