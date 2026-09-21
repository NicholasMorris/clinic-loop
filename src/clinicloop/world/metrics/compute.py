"""Compute metrics from simulation run results."""

from clinicloop.world.engine import RunResult

from .models import MetricSnapshot


def compute_snapshot(run_result: RunResult) -> MetricSnapshot:
    """Compute a MetricSnapshot from a RunResult.

    Args:
        run_result: The result of a simulation run.

    Returns:
        A MetricSnapshot containing throughput, wait times, SLA breaches,
        and cost per order.

    Raises:
        NotImplementedError: This function is not yet implemented.
    """
    raise NotImplementedError("compute_snapshot is not yet implemented")
