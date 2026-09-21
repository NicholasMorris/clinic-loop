"""Staffing configuration and worker pool management."""

import tomllib
from pathlib import Path

from pydantic import BaseModel


class StaffingParameterMissing(Exception):
    """Raised when a required staffing parameter is missing.

    Attributes:
        pool_name: The name of the worker pool.
        key: The missing parameter key.
    """

    def __init__(self, pool_name: str, key: str) -> None:
        """Initialize the exception.

        Args:
            pool_name: The name of the worker pool.
            key: The missing parameter key.
        """
        self.pool_name = pool_name
        self.key = key
        super().__init__(f"Missing parameter '{key}' in pool '{pool_name}'")


class WorkerPoolConfig(BaseModel):
    """Configuration for a worker pool.

    Attributes:
        assumed: Whether the values are assumed (starter values).
        assumption_note: Description of what is assumed.
        service_time_family: Distribution family for service times (e.g., "exponential", "normal").
        mean_service_minutes: Mean service time in minutes for this pool.
        staffing_level: Number of workers in this pool.
        hourly_cost: Cost per hour for this pool.
    """

    assumed: bool
    assumption_note: str
    service_time_family: str
    mean_service_minutes: float
    staffing_level: int
    hourly_cost: float


def load_staffing(config_path: str | Path | None = None) -> dict[str, WorkerPoolConfig]:
    """Load staffing configuration from TOML file.

    Args:
        config_path: Path to the staffing.toml file.
                   If None, uses the default in src/clinicloop/world/config/staffing.toml.

    Returns:
        A dictionary mapping pool names to their configuration.

    Raises:
        StaffingParameterMissing: If a required parameter is missing.
    """
    # Use default path if not provided
    if config_path is None:
        # Get the path to the default staffing.toml
        current_file = Path(__file__).resolve()
        config_path = current_file.parent.parent / "config" / "staffing.toml"
    else:
        config_path = Path(config_path)

    # Read the TOML file
    with open(config_path, "rb") as f:
        config_data = tomllib.load(f)

    # Parse each pool configuration
    result: dict[str, WorkerPoolConfig] = {}
    required_keys = {
        "assumed",
        "assumption_note",
        "service_time_family",
        "mean_service_minutes",
        "staffing_level",
        "hourly_cost",
    }

    for pool_name, pool_data in config_data.items():
        # Check for missing required keys
        missing_keys = required_keys - set(pool_data.keys())
        if missing_keys:
            missing_key = next(iter(missing_keys))
            raise StaffingParameterMissing(pool_name, missing_key)

        # Create WorkerPoolConfig
        result[pool_name] = WorkerPoolConfig(
            assumed=pool_data["assumed"],
            assumption_note=pool_data["assumption_note"],
            service_time_family=pool_data["service_time_family"],
            mean_service_minutes=pool_data["mean_service_minutes"],
            staffing_level=pool_data["staffing_level"],
            hourly_cost=pool_data["hourly_cost"],
        )

    return result
