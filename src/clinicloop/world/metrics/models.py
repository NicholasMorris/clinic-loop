"""Models for metrics computation."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class MetricSnapshot(BaseModel):
    """A frozen, versioned snapshot of metrics for a completed run.

    This model is used to capture metrics about a simulation run at a point
    in time, ensuring that the same input always produces the same output.
    """

    model_config = ConfigDict(frozen=True)
