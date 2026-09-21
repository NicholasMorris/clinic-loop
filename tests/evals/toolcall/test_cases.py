"""Test AC1: Case set has exactly 30 stable cases."""

import pytest

from clinicloop.evals.toolcall.cases import load_cases


def test_case_set_has_thirty_stable_cases() -> None:
    """AC1: The case set contains exactly 30 cases with stable ordering.

    Loading the case set twice yields identical ordered case ids.
    """
    # First load
    cases_1 = load_cases()
    ids_1 = [case["case_id"] for case in cases_1]

    # Check we have exactly 30
    assert len(cases_1) == 30, f"Expected 30 cases, got {len(cases_1)}"

    # Check all case_ids are unique
    assert len(set(ids_1)) == 30, "Case IDs are not unique"

    # Second load
    cases_2 = load_cases()
    ids_2 = [case["case_id"] for case in cases_2]

    # Check ordering is stable
    assert ids_1 == ids_2, "Case IDs are not in stable order across two loads"
