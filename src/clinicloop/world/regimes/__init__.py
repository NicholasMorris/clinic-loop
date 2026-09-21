"""Regime parameters for SimClinic by jurisdiction."""

from .inventory_ids import KNOWN_INVENTORY_IDS
from .registry import get_regime

__all__ = [
    "get_regime",
    "KNOWN_INVENTORY_IDS",
]
