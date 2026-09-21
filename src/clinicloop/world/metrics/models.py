"""Models for metrics computation."""

from pydantic import BaseModel, ConfigDict, Field


class ThroughputMetrics(BaseModel):
    """Throughput metrics for a run.

    Attributes:
        orders_completed: Number of orders that completed pharmacy_fulfilment.
        orders_per_simulated_hour: Throughput as orders per hour of simulation.
    """

    orders_completed: int
    orders_per_simulated_hour: float


class SLABreach(BaseModel):
    """SLA breach record.

    Attributes:
        rule_id: The ID of the SLA rule that was breached.
        count: Number of breaches for this rule.
        inventory_id: The inventory ID cited by the rule.
    """

    rule_id: str
    count: int
    inventory_id: str


class MetricSnapshot(BaseModel):
    """A frozen, versioned snapshot of metrics for a completed run.

    This model is used to capture metrics about a simulation run at a point
    in time, ensuring that the same input always produces the same output.

    Attributes:
        schema_version: Version of this snapshot schema (currently "1").
        throughput: ThroughputMetrics with orders_completed and orders_per_simulated_hour.
        median_wait_minutes: Dict of queue names to median wait minutes (None if no items).
        sla_breaches: List of SLABreach entries keyed by rule_id.
        cost_per_order: Cost per order (busy hours × hourly_cost / orders), or None if zero.
    """

    model_config = ConfigDict(frozen=True)

    schema_version: str = Field(default="1", description="Schema version for this snapshot")
    throughput: ThroughputMetrics
    median_wait_minutes: dict[str, float | None]
    sla_breaches: dict[str, SLABreach]
    cost_per_order: float | None
