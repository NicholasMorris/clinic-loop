"""Compute metrics from simulation run results."""

import statistics
import tomllib
from pathlib import Path

from clinicloop.world.engine import RunResult, sla_rules
from clinicloop.world.workers import load_staffing

from .models import MetricSnapshot, SLABreach, ThroughputMetrics


def compute_snapshot(run_result: RunResult) -> MetricSnapshot:
    """Compute a MetricSnapshot from a RunResult.

    Computes metrics including throughput, median wait per queue, SLA breaches,
    and cost per order from the event log. All computation is deterministic
    from the input RunResult.

    Args:
        run_result: The result of a simulation run.

    Returns:
        A MetricSnapshot containing throughput, wait times, SLA breaches,
        and cost per order.
    """
    # Compute throughput
    throughput = _compute_throughput(run_result)

    # Compute median wait times per queue
    median_waits = _compute_median_waits(run_result)

    # Compute SLA breaches
    breaches = _compute_sla_breaches(run_result)

    # Compute cost per order
    cost_per_order = _compute_cost_per_order(run_result)

    return MetricSnapshot(
        schema_version="1",
        throughput=throughput,
        median_wait_minutes=median_waits,
        sla_breaches=breaches,
        cost_per_order=cost_per_order,
    )


def _compute_throughput(run_result: RunResult) -> ThroughputMetrics:
    """Compute throughput metrics.

    Orders are items that completed pharmacy_fulfilment queue.
    Throughput is orders completed per simulated hour.
    """
    # Count completed orders (items finished in pharmacy_fulfilment)
    completed_orders = sum(
        1
        for record in run_result.records
        if record.queue == "pharmacy_fulfilment" and record.finished_at is not None
    )

    # Compute throughput as orders per simulated hour
    duration_hours = run_result.duration_minutes / 60.0
    if duration_hours > 0:
        orders_per_hour = completed_orders / duration_hours
    else:
        orders_per_hour = 0.0

    return ThroughputMetrics(
        orders_completed=completed_orders,
        orders_per_simulated_hour=orders_per_hour,
    )


def _compute_median_waits(run_result: RunResult) -> dict[str, float | None]:
    """Compute median wait time per queue.

    Wait time is the time until service starts:
    - For started items: started_at - enqueued_at
    - For unstarted items: duration_minutes - enqueued_at

    Only queues with items (started or unstarted) are included.
    Empty queues have None value.
    """
    queue_names = ["intake", "prescriber_review", "pharmacy_fulfilment", "support_inbox"]
    median_waits: dict[str, float | None] = {}

    for queue in queue_names:
        waits = []
        for record in run_result.records:
            if record.queue == queue:
                if record.started_at is not None:
                    # Item started: wait is start time - enqueue time
                    wait = record.started_at - record.enqueued_at
                else:
                    # Item not started: wait is duration - enqueue time
                    wait = run_result.duration_minutes - record.enqueued_at
                waits.append(wait)

        if waits:
            # Compute median for this queue
            median_waits[queue] = statistics.median(waits)
        else:
            # No items in this queue
            median_waits[queue] = None

    return median_waits


def _compute_sla_breaches(run_result: RunResult) -> dict[str, SLABreach]:
    """Compute SLA breaches based on wait time targets.

    Loads per-queue SLA targets from sla_targets.toml.
    A breach occurs when wait time exceeds the target.
    Maps rule IDs to breach counts and inventory IDs from sla_rules().
    """
    # Load SLA targets
    sla_targets = _load_sla_targets()

    # Get the mapping of rule IDs to inventory IDs
    rule_to_inventory = sla_rules()

    breaches: dict[str, SLABreach] = {}

    # For now, we'll map queues to SLA rules based on the issue description
    # termination_cutoff (ps-03): applies to orders (pharmacy_fulfilment queue)
    # dispatch_commitment (po-01): applies to prescriber_review queue

    for record in run_result.records:
        queue = record.queue

        # Skip if no rule for this queue
        if queue not in sla_targets:
            continue

        # Calculate wait time (time until service starts)
        if record.started_at is not None:
            wait = record.started_at - record.enqueued_at
        else:
            wait = run_result.duration_minutes - record.enqueued_at

        target = sla_targets[queue]["target_minutes"]

        # Check if breach
        if wait > target:  # type: ignore[operator]
            # Determine which rule this breach belongs to
            # Map based on the queue and the issue description
            if queue == "pharmacy_fulfilment":
                rule_id = "termination_cutoff"
            elif queue == "prescriber_review":
                rule_id = "dispatch_commitment"
            else:
                # For other queues, skip (not part of the core SLA rules)
                continue

            # Initialize breach if not seen before
            if rule_id not in breaches:
                inventory_id = rule_to_inventory.get(rule_id, "unknown")
                breaches[rule_id] = SLABreach(
                    rule_id=rule_id,
                    count=0,
                    inventory_id=inventory_id,
                )

            # Increment breach count
            breaches[rule_id].count += 1

    return breaches


def _load_sla_targets() -> dict[str, dict[str, float | bool | str]]:
    """Load SLA targets from sla_targets.toml.

    Returns:
        A dictionary mapping queue names to their SLA target configurations.
    """
    # Get the path to sla_targets.toml
    current_file = Path(__file__).resolve()
    config_path = current_file.parent.parent / "config" / "sla_targets.toml"

    with open(config_path, "rb") as f:
        return tomllib.load(f)


def _compute_cost_per_order(run_result: RunResult) -> float | None:
    """Compute cost per order.

    Cost per order = (total staffing cost for busy time) / (completed orders)

    Staffing cost for busy time = sum over queues of (busy_hours * hourly_cost)
    where busy_hours is the total time items were being served in that queue.

    Returns None if zero completed orders to avoid division by zero.
    """
    # Count completed orders
    completed_orders = sum(
        1
        for record in run_result.records
        if record.queue == "pharmacy_fulfilment" and record.finished_at is not None
    )

    if completed_orders == 0:
        return None

    # Load staffing configuration to get hourly costs
    staffing_config = load_staffing()

    # Calculate total busy hours per queue and total cost
    total_cost = 0.0

    for queue in ["intake", "prescriber_review", "pharmacy_fulfilment", "support_inbox"]:
        busy_minutes = 0
        for record in run_result.records:
            if (
                record.queue == queue
                and record.started_at is not None
                and record.finished_at is not None
            ):
                # Busy time for this item in this queue
                service_time = record.finished_at - record.started_at
                busy_minutes += service_time

        # Convert to hours
        busy_hours = busy_minutes / 60.0

        # Get hourly cost for this queue
        hourly_cost = staffing_config[queue].hourly_cost

        # Add to total cost
        total_cost += busy_hours * hourly_cost

    # Compute cost per order
    cost_per_order = total_cost / completed_orders

    return cost_per_order
