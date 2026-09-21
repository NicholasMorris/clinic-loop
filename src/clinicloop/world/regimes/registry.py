"""Regime registry and parameter resolution."""

from typing import Any, Literal


class RegimeParameterNotSet(Exception):
    """Raised when a parameter is not set for a regime.

    This exception is raised when attempting to read a parameter from a regime
    that is marked as a placeholder and does not have that parameter implemented.
    """

    pass


def get_regime(
    regime_key: Literal["au", "nz", "uk"],
) -> Any:
    """Get a regime by key.

    Args:
        regime_key: The regime key ("au", "nz", or "uk").

    Returns:
        The regime object.

    Raises:
        NotImplementedError: This stub must be implemented.
    """
    raise NotImplementedError("get_regime stub")
