"""Test that draft acceptance is correctly labelled as a proxy."""

from clinicloop.compliance.rulesets import load_ruleset
from evals.triage.golden.loader import load_golden_cases, load_intent_elements
from evals.triage.metrics import aggregate_metrics
from evals.triage.runner import run_all


def test_draft_acceptance_is_labelled_a_proxy() -> None:
    """AC4: Metric is draft_acceptance_rate_proxy; no draft_acceptance_rate key exists."""
    cases = load_golden_cases()
    elements = load_intent_elements()
    ruleset = load_ruleset("au")

    # Run a small subset to get some artifacts
    artifacts = run_all(cases[:5], ruleset, elements)

    # Compute aggregate
    metrics = aggregate_metrics(artifacts)

    # Check that draft_acceptance_rate_proxy exists
    assert "draft_acceptance_rate_proxy" in metrics, (
        f"Expected 'draft_acceptance_rate_proxy' in metrics, got keys: {metrics.keys()}"
    )

    # Check that draft_acceptance_rate (without _proxy) does NOT exist
    assert "draft_acceptance_rate" not in metrics, (
        f"Should not have 'draft_acceptance_rate' (without _proxy) in metrics, "
        f"got keys: {metrics.keys()}"
    )

    # Check review_method on each artifact
    for artifact in artifacts:
        assert artifact.review_method == "rule-based reference reviewer", (
            f"Expected review_method='rule-based reference reviewer', got {artifact.review_method}"
        )
