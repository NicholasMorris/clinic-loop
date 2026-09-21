"""Conformance tests for M2-1: guard corpus and baseline checks."""

import pytest

from clinicloop.evals.core.registry import get_metric
from clinicloop.evals.guard import FAMILIES, MIN_PER_FAMILY, load_cases


@pytest.mark.checklist_id("R1")
def test_R1_corpus_covers_all_rule_families() -> None:
    """R1: Corpus has block cases for all five rule ids across families."""
    cases = load_cases()

    # Collect all block cases
    block_cases = [c for c in cases if c.expected_verdict == "block"]
    rule_ids_present = {c.expected_rule_id for c in block_cases}

    # Check all five rule ids present
    expected_rules = {
        "AU-G-PRODUCT",
        "AU-G-EUPHEMISM",
        "AU-G-DOSE",
        "AU-G-CONDITION",
        "AU-G-ADVICE",
    }

    missing_rules = expected_rules - rule_ids_present
    assert missing_rules == set(), f"Missing rule ids: {missing_rules}"

    # Check each family has >=12 block cases
    for family in FAMILIES:
        family_blocks = [c for c in block_cases if c.family == family]
        assert len(family_blocks) >= MIN_PER_FAMILY, (
            f"{family}: {len(family_blocks)} < {MIN_PER_FAMILY}"
        )


@pytest.mark.checklist_id("E1")
def test_E1_guard_component_registered() -> None:
    """E1: Guard component registered in registry with zero violation threshold."""
    from clinicloop.evals.guard.metric import register_guard_metric

    register_guard_metric()  # idempotent; other tests may have cleared the registry
    entry = get_metric("guard", "rule_violation_rate")
    assert entry is not None, "guard/rule_violation_rate not registered"

    metric_func, threshold = entry
    assert threshold == 0.0, f"Expected threshold 0.0, got {threshold}"


@pytest.mark.checklist_id("X4")
def test_X4_append_only_removal_raises() -> None:
    """X4: Removing a case id from prior manifest raises AppendOnlyViolation."""
    from clinicloop.evals.core.artifacts import AppendOnlyViolation
    from clinicloop.evals.guard import append_only_diff, manifest_of

    cases = load_cases()
    current = manifest_of(cases)

    # Prior with extra case
    prior = current.copy()
    prior["fake-removal"] = "allow"

    # Should raise
    with pytest.raises(AppendOnlyViolation):
        append_only_diff(prior, current)
