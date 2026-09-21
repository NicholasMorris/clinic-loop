"""Cohort generator with equal true base rates and planted confounds."""

from typing import Any


def generate_cohorts(
    seed: int,
    count: int | None = None,
    cases_per_cohort: int | None = None,
) -> tuple[list[dict[str, Any]], list[tuple[str, set[str], set[str]]]]:
    """Generate cohorts with equal true base rates and planted confounds.

    Args:
        seed: Random seed for reproducibility.
        count: Number of cohorts (overrides config if provided).
        cases_per_cohort: Cases per cohort (overrides config if provided).

    Returns:
        A tuple of (cohorts, ground_truth) where:
        - cohorts is a list of cohort dictionaries with 'identity' and 'cases'
        - ground_truth is a list of (patient_id, signals_set, confounds_set)
    """
    raise NotImplementedError("generate_cohorts not yet implemented")
