"""Conformance tests for M2-6a triage evaluation."""

from clinicloop.compliance.rulesets import load_ruleset
from evals.triage.golden.loader import load_golden_cases, load_intent_elements
from evals.triage.metrics import register_triage_metrics


def test_e1_metrics_registration():
    """E1: Triage metrics are registered and can be retrieved."""
    from clinicloop.evals.core.registry import get_metric

    # Register the metrics
    register_triage_metrics()

    # Verify they can be retrieved
    intent_acc = get_metric("triage", "intent_accuracy")
    escalation_rec = get_metric("triage", "escalation_recall")
    rule_viol = get_metric("triage", "rule_violation_rate")
    draft_accept = get_metric("triage", "draft_acceptance_rate_proxy")

    assert intent_acc is not None, "intent_accuracy metric not registered"
    assert escalation_rec is not None, "escalation_recall metric not registered"
    assert rule_viol is not None, "rule_violation_rate metric not registered"
    assert draft_accept is not None, "draft_acceptance_rate_proxy metric not registered"


def test_c1_escalating_case_produces_artifact():
    """C1: Escalating case produces artifact with escalation_category and no draft hash."""
    cases = load_golden_cases()
    elements = load_intent_elements()
    ruleset = load_ruleset("au")

    # Find a case with escalation_category != 'none'
    escalating_cases = [c for c in cases if c.escalation_category != "none"]
    assert escalating_cases, "Need at least one escalating case"

    escalating_case = escalating_cases[0]

    # Run the case
    from evals.triage.runner import run_case

    artifact = run_case(escalating_case, ruleset, elements)

    # Verify escalation category is set
    assert artifact.escalation_category == escalating_case.escalation_category, (
        f"Expected escalation_category={escalating_case.escalation_category}, "
        f"got {artifact.escalation_category}"
    )

    # Verify draft_text_sha256 is None (escalating cases don't produce drafts)
    assert artifact.draft_text_sha256 is None, (
        f"Expected draft_text_sha256=None for escalating case, got {artifact.draft_text_sha256}"
    )


def test_x4_golden_set_and_docs_exist():
    """X4: Golden set exists with floor of 5 per intent/category; docs exist."""
    from pathlib import Path

    cases = load_golden_cases()

    # Check counts
    intent_counts = {}
    for case in cases:
        intent_counts[case.intent] = intent_counts.get(case.intent, 0) + 1

    for intent, count in intent_counts.items():
        assert count >= 5, f"Intent {intent} has only {count} cases, need >= 5"

    escalation_counts = {}
    for case in cases:
        escalation_counts[case.escalation_category] = (
            escalation_counts.get(case.escalation_category, 0) + 1
        )

    for escalation, count in escalation_counts.items():
        assert count >= 5, f"Escalation {escalation} has only {count} cases, need >= 5"

    # Verify docs exist
    docs_path = Path(__file__).parent.parent.parent / "docs" / "evaluation" / "triage.md"
    assert docs_path.exists(), f"docs/evaluation/triage.md not found at {docs_path}"
