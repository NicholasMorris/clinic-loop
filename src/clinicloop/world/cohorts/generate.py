"""Cohort generator with equal true base rates and planted confounds."""

from typing import Any

import numpy as np

from ..generator import generate_world
from .profile import load_cohort_profile


def generate_cohorts(
    seed: int,
    count: int | None = None,
    cases_per_cohort: int | None = None,
) -> tuple[list[dict[str, Any]], list[tuple[str, set[str], set[str]]]]:
    """Generate cohorts with equal true base rates and planted confounds.

    Creates multiple cohorts where each cohort is distinguished by a dense
    confound. Signals are planted with equal base rates across all cohorts.
    Confounds (e.g., shared payment instruments, address churn) are denser in
    their assigned cohort than in others.

    Args:
        seed: Random seed for reproducibility.
        count: Number of cohorts (overrides config if provided).
        cases_per_cohort: Cases per cohort (overrides config if provided).

    Returns:
        A tuple of (cohorts, ground_truth) where:
        - cohorts is a list of cohort dictionaries with 'identity' and 'cases'
        - ground_truth is a list of (patient_id, signals_set, confounds_set)
            where signals_set and confounds_set are sets of planted types
    """
    # Load configuration
    profile = load_cohort_profile()
    cohort_count = count or profile.cohort_count
    cases_per_cohort_count = cases_per_cohort or profile.cases_per_cohort

    # Confound identities for each cohort
    confound_identities = [
        "household_shared_instrument",
        "renter_address_churn",
        "transliteration_variance",
        "first_january_dob",
    ]

    # Pad with multigenerational_instrument if needed
    while len(confound_identities) < cohort_count:
        confound_identities.append("multigenerational_instrument")

    # Generate world with all patients
    total_patients = cohort_count * cases_per_cohort_count
    world = generate_world(seed=seed, population_size=total_patients, span_days=365)

    # Set up RNG for plant decisions
    rng = np.random.Generator(np.random.PCG64(seed))

    # Ground truth storage: (patient_id, signals_set, confounds_set)
    ground_truth: list[tuple[str, set[str], set[str]]] = []

    # Target signal base rate (same for all cohorts)
    target_signal_rate = 0.15  # 15% of patients should have the signal

    # Confound rates: higher in dense cohort, lower in others
    dense_confound_rate = 0.3  # 30% in the dense cohort
    sparse_confound_rate = 0.05  # 5% in other cohorts

    # Create cohort data structures
    cohorts: list[dict[str, Any]] = []

    # Assign patients to cohorts and plant signals/confounds
    signals_planted_per_cohort: dict[int, list[tuple[int, str]]] = {
        i: [] for i in range(cohort_count)
    }
    confounds_planted_per_cohort: dict[int, list[tuple[int, str]]] = {
        i: [] for i in range(cohort_count)
    }

    # First pass: assign patients to cohorts
    for cohort_idx in range(cohort_count):
        cohort_data: dict[str, Any] = {
            "identity": confound_identities[cohort_idx % len(confound_identities)],
            "cases": [],
        }

        start_idx = cohort_idx * cases_per_cohort_count
        end_idx = start_idx + cases_per_cohort_count

        for patient_idx in range(start_idx, end_idx):
            patient = world.patients[patient_idx]

            # Create case record without cohort label or protected attributes
            # (no date_of_birth, postcode, address, or other demographic info)
            case: dict[str, str] = {
                "patient_id": patient.patient_id,
                "phone_number": patient.phone_number,
                "email": patient.email,
                "payment_instrument_id": patient.payment_instrument_id,
                "market": patient.market,
            }

            cohort_data["cases"].append(case)

        cohorts.append(cohort_data)

    # Second pass: plant signals and confounds
    signal_types = [
        "duplicate_identity",
        "reused_instrument",
        "template_language",
        "consult_shopping",
        "velocity",
    ]

    confound_types = {
        "household_shared_instrument",
        "renter_address_churn",
        "transliteration_variance",
        "first_january_dob",
        "multigenerational_instrument",
    }

    # Plant signals with equal base rates across all cohorts
    # For each signal type, we distribute it equally across all cohorts
    signals_per_cohort = int(cases_per_cohort_count * target_signal_rate)

    for signal_type in signal_types:
        # For each cohort, select the same number of patients to plant this signal
        for cohort_idx in range(cohort_count):
            # Get indices of patients to plant this signal in this cohort
            patient_indices = rng.choice(
                cases_per_cohort_count, size=signals_per_cohort, replace=False
            )
            for local_idx in patient_indices:
                signals_planted_per_cohort[cohort_idx].append((local_idx, signal_type))

    # Plant confounds with higher density in the dense cohort
    for cohort_idx in range(cohort_count):
        dense_confound = confound_identities[cohort_idx % len(confound_identities)]

        for local_idx in range(cases_per_cohort_count):
            patient_idx = cohort_idx * cases_per_cohort_count + local_idx

            # Check dense confound
            if rng.random() < dense_confound_rate:
                confounds_planted_per_cohort[cohort_idx].append((local_idx, dense_confound))

            # Check other confounds with sparse rate
            for other_confound in confound_types:
                if other_confound != dense_confound:
                    if rng.random() < sparse_confound_rate:
                        confounds_planted_per_cohort[cohort_idx].append((local_idx, other_confound))

    # Build ground truth
    for cohort_idx in range(cohort_count):
        for local_idx in range(cases_per_cohort_count):
            patient_idx = cohort_idx * cases_per_cohort_count + local_idx
            patient = world.patients[patient_idx]

            # Collect signals for this patient
            signals = set()
            for pidx, signal in signals_planted_per_cohort[cohort_idx]:
                if pidx == local_idx:
                    signals.add(signal)

            # Collect confounds for this patient
            confounds = set()
            for pidx, confound in confounds_planted_per_cohort[cohort_idx]:
                if pidx == local_idx:
                    confounds.add(confound)

            ground_truth.append((patient.patient_id, signals, confounds))

    return cohorts, ground_truth
