"""Test that cohort labels are separated from case records."""

import pytest

from clinicloop.world.cohorts import generate_cohorts


def test_case_records_do_not_carry_cohort_labels() -> None:
    """Test that cohort membership labels are not in case records.

    Cohort membership labels are written to a separate evaluation-only export
    that case records do not reference, so a case record carries no cohort
    label field.
    """
    cohorts, ground_truth = generate_cohorts(seed=20260921)

    cohort_label_names = {
        "cohort",
        "cohort_id",
        "cohort_label",
        "cohort_name",
        "group",
        "treatment_group",
    }

    for cohort_idx, cohort_data in enumerate(cohorts):
        # Check case records do not contain cohort labels
        for case in cohort_data.get("cases", []):
            for key in case.keys():
                assert key.lower() not in cohort_label_names, (
                    f"Cohort {cohort_idx} case contains cohort label field: {key}"
                )
