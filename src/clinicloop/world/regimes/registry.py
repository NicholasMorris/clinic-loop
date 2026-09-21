"""Regime registry and parameter resolution."""

from typing import Any, Literal, NamedTuple

from .inventory_ids import KNOWN_INVENTORY_IDS


class RegimeParameterNotSet(Exception):
    """Raised when a parameter is not set for a regime.

    This exception is raised when attempting to read a parameter from a regime
    that is marked as a placeholder and does not have that parameter implemented.
    """

    pass


class ConflictEntry(NamedTuple):
    """A recorded conflict in regime parameters.

    Attributes:
        inventory_id: The inventory ID of the conflicted parameter (e.g., "x-01").
        alternative_value: The alternative value mentioned in the inventory.
    """

    inventory_id: str
    alternative_value: tuple[int, int]


class RegimeParameter(NamedTuple):
    """A single parameter in a regime.

    Attributes:
        value: The parameter value.
        inventory_ids: Tuple of inventory IDs this parameter cites.
    """

    value: Any
    inventory_ids: tuple[str, ...]


class Regime:
    """Base class for regime parameters.

    A regime encapsulates jurisdiction-specific parameters for SimClinic,
    such as shipping costs, SLAs, and consultation requirements.
    """

    def __init__(
        self,
        regime_key: str,
        parameters_status: str,
        params: dict[str, tuple[Any, tuple[str, ...]]] | None = None,
        recorded_conflicts: list[ConflictEntry] | None = None,
    ) -> None:
        """Initialize a Regime.

        Args:
            regime_key: The regime key ("au", "nz", "uk").
            parameters_status: Status of parameters ("populated" or "placeholder").
            params: Dictionary of parameter_name -> (value, inventory_ids_tuple).
            recorded_conflicts: List of recorded conflicts in this regime.
        """
        self.regime_key = regime_key
        self.parameters_status = parameters_status
        self._params = params or {}
        self.recorded_conflicts = recorded_conflicts or []

    def __getattr__(self, name: str) -> Any:
        """Get a parameter value.

        Args:
            name: Parameter name.

        Returns:
            The parameter value.

        Raises:
            RegimeParameterNotSet: If the regime is a placeholder and the parameter is not set.
            AttributeError: If the attribute does not exist.
        """
        if name.startswith("_"):
            raise AttributeError(f"Regime has no attribute {name}")

        if name in self._params:
            return self._params[name][0]

        if self.parameters_status == "placeholder":
            raise RegimeParameterNotSet(
                f"Parameter '{name}' is not set for regime '{self.regime_key}' "
                f"(status: placeholder)"
            )

        raise AttributeError(f"Regime '{self.regime_key}' has no parameter '{name}'")


def _validate_inventory_ids(ids: tuple[str, ...]) -> None:
    """Validate that all inventory IDs are in KNOWN_INVENTORY_IDS.

    Args:
        ids: The inventory IDs to validate.

    Raises:
        ValueError: If any ID is not in KNOWN_INVENTORY_IDS.
    """
    unknown_ids = set(ids) - KNOWN_INVENTORY_IDS
    if unknown_ids:
        raise ValueError(f"Unknown inventory IDs: {unknown_ids}")


def _create_au_regime() -> Regime:
    """Create the AU (Australia) regime with populated parameters."""
    params: dict[str, tuple[Any, tuple[str, ...]]] = {
        "flat_shipping_cents": (995, ("po-01",)),
        "free_shipping_threshold_cents": (12900, ("po-01",)),
        "termination_cutoff_business_days": (2, ("ps-03",)),
        "damage_report_window_days": (3, ("ps-04",)),
        "consultation_validity_months": (6, ("po-02",)),
        "delivery_working_days": ((4, 5), ("po-06",)),
        "dispatch_commitment_business_days": (1, ("po-02",)),
    }

    # Validate all inventory IDs
    for _, (_, ids) in params.items():
        _validate_inventory_ids(ids)

    recorded_conflicts = [
        ConflictEntry(inventory_id="x-01", alternative_value=(2, 5)),
    ]

    return Regime(
        regime_key="au",
        parameters_status="populated",
        params=params,
        recorded_conflicts=recorded_conflicts,
    )


def _create_nz_regime() -> Regime:
    """Create the NZ (New Zealand) regime as a placeholder."""
    return Regime(
        regime_key="nz",
        parameters_status="placeholder",
    )


def _create_uk_regime() -> Regime:
    """Create the UK (United Kingdom) regime as a placeholder."""
    return Regime(
        regime_key="uk",
        parameters_status="placeholder",
    )


# Global regime registry
_REGIMES: dict[str, Regime] = {
    "au": _create_au_regime(),
    "nz": _create_nz_regime(),
    "uk": _create_uk_regime(),
}


def get_regime(
    regime_key: Literal["au", "nz", "uk"],
) -> Regime:
    """Get a regime by key.

    Args:
        regime_key: The regime key ("au", "nz", or "uk").

    Returns:
        The regime object.
    """
    return _REGIMES[regime_key]
