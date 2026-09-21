"""Staffing configuration and worker pool management."""

from pathlib import Path
from typing import Any

import tomli
from pydantic import BaseModel, Field


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
        staffing_level: Number of workers in this pool.
        hourly_cost: Cost per hour for this pool.
    """

    assumed: bool
    assumption_note: str
    service_time_family: str
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
        NotImplementedError: Stub implementation.
        StaffingParameterMissing: If a required parameter is missing.
    """
    raise NotImplementedError("load_staffing")
