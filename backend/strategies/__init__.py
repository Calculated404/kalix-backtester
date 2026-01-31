from backend.strategies.base import get_strategy_class, list_strategies
from backend.strategies.mean_reversion import MeanReversionStrategy
from backend.strategies.trend_following import TrendFollowingStrategy
from backend.strategies.double_rsi_strategy import DoubleRSIStrategy
from backend.strategies.tmv_strategy import TMVStrategy

__all__ = [
    "get_strategy_class",
    "list_strategies",
    "MeanReversionStrategy",
    "TrendFollowingStrategy",
    "DoubleRSIStrategy",
    "TMVStrategy",
]

# Strategy display names and descriptions
STRATEGY_INFO = {
    "trend_momentum_volume": {
        "display_name": "Trend + Momentum + Volume (TMV)",
        "short_name": "TMV",
        "description": "Multi-factor strategy combining trend, momentum, and volume"
    },
    "mean_reversion": {
        "display_name": "Mean Reversion",
        "short_name": "Mean Reversion",
        "description": "Bollinger Bands + RSI bounce strategy"
    },
    "trend_following": {
        "display_name": "Trend Following",
        "short_name": "Trend Following",
        "description": "SMA crossover + MACD confirmation"
    },
    "double_rsi": {
        "display_name": "Double RSI",
        "short_name": "Double RSI",
        "description": "Dual-timeframe RSI for trend and signals"
    }
}
