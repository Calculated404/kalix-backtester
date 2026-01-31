"""Base strategy interface and registry for Backtesting.py."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from backtesting import Strategy

REGISTRY: dict[str, Type["Strategy"]] = {}
LOG = logging.getLogger(__name__)


def register(name: str):
    """Decorator to register a strategy class by name."""

    def _register(cls: Type["Strategy"]) -> Type["Strategy"]:
        REGISTRY[name] = cls
        return cls

    return _register


def get_strategy_class(name: str) -> Type["Strategy"]:
    if name not in REGISTRY:
        raise ValueError(f"Unknown strategy: {name}. Available: {list(REGISTRY.keys())}")
    return REGISTRY[name]


def list_strategies() -> list[str]:
    return list(REGISTRY.keys())
