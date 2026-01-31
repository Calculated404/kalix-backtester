from backend.strategies.base import get_strategy_class, list_strategies
from backend.strategies.mean_reversion import MeanReversionStrategy
from backend.strategies.trend_following import TrendFollowingStrategy

__all__ = [
    "get_strategy_class",
    "list_strategies",
    "MeanReversionStrategy",
    "TrendFollowingStrategy",
]
