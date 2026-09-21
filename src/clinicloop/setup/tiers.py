"""Hardware tier detection and resolution."""

from pathlib import Path
from typing import Any


class UnsupportedMemoryTier(Exception):
    """Raised when available memory does not match any supported tier."""

    pass


def get_available_memory_gib() -> int:
    """Detect available system memory in GiB.

    Returns:
        Available memory in GiB.
    """
    raise NotImplementedError


def load_tiers(config_path: Path) -> list[dict[str, Any]]:
    """Load hardware tiers from TOML configuration file.

    Args:
        config_path: Path to hardware_tiers.toml file.

    Returns:
        List of tier dictionaries with keys: label, min_gib, repo_id,
        quantisation, fallback_repo_id, provenance.

    Raises:
        ValueError: If validation fails (e.g., missing required key).
    """
    raise NotImplementedError


def resolve_tier(tiers: list[dict[str, Any]]) -> dict[str, Any]:
    """Resolve the appropriate tier based on available memory.

    Args:
        tiers: List of tier dictionaries from load_tiers().

    Returns:
        The selected tier dictionary for the detected memory amount.

    Raises:
        UnsupportedMemoryTier: If available memory is below the lowest tier.
    """
    raise NotImplementedError
