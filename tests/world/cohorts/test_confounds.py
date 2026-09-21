"""Test that all five confound kinds are planted in cohorts."""

import pytest

from clinicloop.world.cohorts import generate_cohorts


def test_all_five_confound_kinds_are_planted() -> None:
    """Test that all five confound types are present in generated cohorts.

    Enumerating the ground truth over a generated set yields at least one case
    for each of household_shared_instrument, renter_address_churn,
    transliteration_variance, first_january_dob and multigenerational_instrument.
    """
    cohorts, ground_truth = generate_cohorts(seed=20260921)

    confound_types = {
        "household_shared_instrument",
        "renter_address_churn",
        "transliteration_variance",
        "first_january_dob",
        "multigenerational_instrument",
    }

    found_confounds = set()

    for patient_id, signals_set, confounds_set in ground_truth:
        for confound in confounds_set:
            if confound in confound_types:
                found_confounds.add(confound)

    for confound_type in confound_types:
        assert confound_type in found_confounds, (
            f"Confound type {confound_type} not found in ground truth"
        )

    assert confound_types == found_confounds
