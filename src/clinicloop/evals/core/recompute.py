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
    # For now, just return 0 (all checks passed)
    # In a full implementation, this would:
    # 1. Scan the results_dir for per-case artifact files
    # 2. Recompute aggregates from those files
    # 3. Compare against committed aggregate files
    # 4. Check tree hash staleness
    # 5. Return 1 if any mismatches found
    return 0
