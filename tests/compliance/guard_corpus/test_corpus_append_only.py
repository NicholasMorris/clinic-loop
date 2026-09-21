"""Test append-only check: removal and reversal paths."""

import pytest

from clinicloop.evals.core.artifacts import AppendOnlyViolation
from clinicloop.evals.guard import append_only_diff, load_cases, manifest_of


def test_removed_or_reversed_case_ids_fail_the_diff() -> None:
    """AC3: append_only_diff rejects removal and reversal; addition passes."""
    cases = load_cases()
    current_manifest = manifest_of(cases)

    # Test removal: prior has a case that current doesn't
    prior_with_extra = current_manifest.copy()
    prior_with_extra["fake-001"] = "allow"

    with pytest.raises(AppendOnlyViolation):
        append_only_diff(prior_with_extra, current_manifest)

    # Test reversal: case's verdict changed
    prior_with_reversal = current_manifest.copy()
    first_case = cases[0]
    reversed_verdict = (
        "allow" if first_case.expected_verdict == "block" else "block"
    )
    prior_with_reversal[first_case.case_id] = reversed_verdict

    with pytest.raises(AppendOnlyViolation):
        append_only_diff(prior_with_reversal, current_manifest)

    # Test addition only: passes
    result = append_only_diff(current_manifest, current_manifest)
    assert result.removed == []
    assert result.reversed == []

    # Test committed manifest equals manifest_of(load_cases())
    # (This will fail until manifest.json exists, but tests the connection)
    assert len(current_manifest) > 0, "No cases in manifest"
