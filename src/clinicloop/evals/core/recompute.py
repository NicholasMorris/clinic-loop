"""Recompute script for aggregate values and staleness detection."""

from pathlib import Path


def recompute(results_dir: Path) -> int:
    """Recompute aggregates from per-case files and check staleness.

    Exits with status 1 if any committed aggregate differs from the recomputed
    value or if the tree hash differs from the recorded one.

    Args:
        results_dir: The results directory path.

    Returns:
        0 if all aggregates match and tree hash is current, 1 otherwise.
    """
    raise NotImplementedError
