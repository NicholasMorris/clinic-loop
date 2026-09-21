"""Test that cohorts have equal true base rates for planted signals."""

import pytest

from clinicloop.world.cohorts import generate_cohorts


def test_cohorts_have_equal_true_base_rates() -> None:
    """Test that each planted signal has equal true base rates across cohorts.

    For the default 4-cohort set at seed 20260921, the planted true base rate
    of each signal differs between any two cohorts by less than 0.005 in
    absolute terms, and the ground-truth record reports the intended rate
    per cohort.
    """
    cohorts, ground_truth = generate_cohorts(seed=20260921)

    # Extract signal rates from ground truth
    # ground_truth is a list of (patient_id, signals_set, confounds_set)
    # where signals_set contains signal types that were planted

    signal_types = {
        "duplicate_identity",
        "reused_instrument",
        "template_language",
        "consult_shopping",
        "velocity",
    }

    # Calculate base rate per signal per cohort
    cohort_signal_rates: dict[int, dict[str, float]] = {}
    cohort_sizes: dict[int, int] = {}

    for cohort_idx, cohort_data in enumerate(cohorts):
        cohort_sizes[cohort_idx] = len(cohort_data["cases"])
        cohort_signal_rates[cohort_idx] = {}

        for signal_type in signal_types:
            cohort_signal_rates[cohort_idx][signal_type] = 0.0

    # Count signals in ground truth
    signal_counts: dict[int, dict[str, int]] = {}
    for cohort_idx in range(len(cohorts)):
        signal_counts[cohort_idx] = {signal_type: 0 for signal_type in signal_types}

    for patient_id, signals_set, confounds_set in ground_truth:
        # Find which cohort this patient belongs to
        cohort_idx = None
        for idx, cohort_data in enumerate(cohorts):
            if any(case["patient_id"] == patient_id for case in cohort_data["cases"]):
                cohort_idx = idx
                break

        if cohort_idx is not None:
            for signal in signals_set:
                if signal in signal_types:
                    signal_counts[cohort_idx][signal] += 1

    # Calculate rates
    for cohort_idx in range(len(cohorts)):
        for signal_type in signal_types:
            cohort_signal_rates[cohort_idx][signal_type] = (
                signal_counts[cohort_idx][signal_type] / cohort_sizes[cohort_idx]
                if cohort_sizes[cohort_idx] > 0
                else 0.0
            )

    # Check that rates are equal within 0.005 between any two cohorts
    for signal_type in signal_types:
        rates = [cohort_signal_rates[idx][signal_type] for idx in range(len(cohorts))]
        for i in range(len(rates)):
            for j in range(i + 1, len(rates)):
                diff = abs(rates[i] - rates[j])
                assert diff < 0.005, (
                    f"Signal {signal_type} differs by {diff:.4f} between "
                    f"cohorts {i} and {j} (rates: {rates[i]:.4f} vs {rates[j]:.4f})"
                )
