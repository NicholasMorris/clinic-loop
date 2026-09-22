"""Aggregate metrics computation for triage evaluation."""

from typing import Any

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
    raise NotImplementedError("aggregate_metrics not yet implemented")


def register_triage_metrics() -> None:
    """Register the four triage metrics in the global registry.

    Registers under component 'triage' with placeholder thresholds.
    """
    raise NotImplementedError("register_triage_metrics not yet implemented")
