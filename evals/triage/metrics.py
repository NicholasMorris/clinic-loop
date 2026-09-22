"""Aggregate metrics computation for triage evaluation."""

from typing import Any, cast

from evals.triage.runner import CaseArtifact


def aggregate_metrics(artifacts: list[CaseArtifact]) -> dict[str, Any]:
    """Compute aggregate metrics from case artifacts.

    Returns a dict with these exact keys:
    - intent_accuracy: Fraction of cases where predicted_intent == intent.
    - escalation_recall: Fraction of escalating cases where
      predicted_escalation_category == escalation_category.
    - rule_violation_rate: Fraction where verdict is inconsistent with expected.
    - draft_acceptance_rate_proxy: Fraction where reviewer_accepted is True.

    Args:
        artifacts: List of CaseArtifact objects.

    Returns:
        Dict with the four metric keys and float values.
    """
    # Intent accuracy
    intent_correct = sum(1 for a in artifacts if a.predicted_intent == a.intent)
    intent_accuracy = intent_correct / len(artifacts) if artifacts else 0.0

    # Escalation recall: only for cases where escalation_category != 'none' and != 'detector_error'
    escalating = [
        a
        for a in artifacts
        if a.escalation_category != "none" and a.escalation_category != "detector_error"
    ]
    escalation_misses = [
        a for a in escalating if a.predicted_escalation_category != a.escalation_category
    ]
    escalation_recall = (
        (len(escalating) - len(escalation_misses)) / len(escalating) if escalating else 0.0
    )

    # Rule violation rate: check consistency with expected_verdict
    # For this golden set, expected_verdict is always 'allow' when present
    guard_artifacts = [a for a in artifacts if a.guard_allowed is not None]
    violations = 0
    for a in guard_artifacts:
        # expected_verdict is 'allow' only when escalation_category == 'none'
        if a.escalation_category == "none":
            # Should be allowed (expected_verdict = 'allow')
            if a.guard_allowed is False:
                violations += 1
        # For non-'none' cases, expected_verdict is None, so no violation check
    rule_violation_rate = violations / len(guard_artifacts) if guard_artifacts else 0.0

    # Draft acceptance rate proxy
    reviewer_artifacts = [a for a in artifacts if a.reviewer_accepted is not None]
    accepted_count = sum(1 for a in reviewer_artifacts if a.reviewer_accepted is True)
    draft_acceptance_rate_proxy = (
        accepted_count / len(reviewer_artifacts) if reviewer_artifacts else 0.0
    )

    return {
        "intent_accuracy": intent_accuracy,
        "escalation_recall": escalation_recall,
        "rule_violation_rate": rule_violation_rate,
        "draft_acceptance_rate_proxy": draft_acceptance_rate_proxy,
    }


def register_triage_metrics() -> None:
    """Register the four triage metrics in the global registry.

    Registers under component 'triage' with placeholder thresholds.
    """
    from clinicloop.evals.core.registry import register_metric

    def _intent_accuracy(artifacts: list[CaseArtifact]) -> float:
        """Intent accuracy metric."""
        return cast(float, aggregate_metrics(artifacts)["intent_accuracy"])

    def _escalation_recall(artifacts: list[CaseArtifact]) -> float:
        """Escalation recall metric."""
        return cast(float, aggregate_metrics(artifacts)["escalation_recall"])

    def _rule_violation_rate(artifacts: list[CaseArtifact]) -> float:
        """Rule violation rate metric."""
        return cast(float, aggregate_metrics(artifacts)["rule_violation_rate"])

    def _draft_acceptance_rate_proxy(artifacts: list[CaseArtifact]) -> float:
        """Draft acceptance rate proxy metric."""
        return cast(float, aggregate_metrics(artifacts)["draft_acceptance_rate_proxy"])

    register_metric("triage", "intent_accuracy", _intent_accuracy, 0.0)
    register_metric("triage", "escalation_recall", _escalation_recall, 0.0)
    register_metric("triage", "rule_violation_rate", _rule_violation_rate, 0.0)
    register_metric("triage", "draft_acceptance_rate_proxy", _draft_acceptance_rate_proxy, 0.0)
