"""Compute metrics from backtest stats and trades."""
from __future__ import annotations

from typing import Any, Optional


def compute_metrics(stats_dict: dict[str, Any], trades: list[dict], initial_cash: Optional[float] = None) -> dict[str, Any]:
    """Build metrics summary: win rate, total return, max dd, num trades, avg per week, profit factor, expectancy."""
    n = len(trades)
    wins = [t for t in trades if (t.get("pnl") or t.get("return_pct", 0)) > 0]
    win_rate = (len(wins) / n * 100) if n else 0.0
    
    # Extract financial metrics from backtesting.py stats
    # Use provided initial_cash if available, otherwise try to get from stats
    if initial_cash is not None:
        start_cash = float(initial_cash)
    else:
        start_cash = float(stats_dict.get("Start Cash", 0) or 0)
        
    final_equity = float(stats_dict.get("Equity Final [$]", 0) or 0)
    
    # If final equity is missing but we have start cash and trades, calculate it
    if final_equity == 0 and start_cash > 0:
        total_pnl = sum(t.get("pnl", 0) or 0 for t in trades)
        final_equity = start_cash + total_pnl

    total_return = float(stats_dict.get("Return [%]", 0) or 0)
    max_dd = float(stats_dict.get("Max. Drawdown [%]", 0) or 0)
    
    weeks = 1
    if stats_dict.get("Duration"):
        try:
            days = getattr(stats_dict["Duration"], "days", None) or 0
            weeks = max(1, days / 7)
        except Exception:
            pass
    avg_per_week = n / weeks if weeks else 0
    
    gross_profit = sum(t.get("pnl", 0) or 0 for t in wins)
    losses = [t for t in trades if (t.get("pnl") or 0) < 0]
    gross_loss = abs(sum(t.get("pnl", 0) or 0 for t in losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss else (float("inf") if gross_profit else 0)
    avg_pnl = (sum(t.get("pnl", 0) or 0 for t in trades) / n) if n else 0
    
    return {
        "start_cash": round(start_cash, 2),
        "final_equity": round(final_equity, 2),
        "net_profit": round(final_equity - start_cash, 2),
        "win_rate_pct": round(win_rate, 2),
        "total_return_pct": round(total_return, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "num_trades": n,
        "avg_trades_per_week": round(avg_per_week, 2),
        "profit_factor": round(profit_factor, 2) if isinstance(profit_factor, float) else profit_factor,
        "expectancy_per_trade": round(avg_pnl, 4),
    }
