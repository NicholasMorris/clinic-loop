"""Escalation detection engine."""

from typing import Callable, Optional

from clinicloop.compliance.escalation.result import EscalationResult
from clinicloop.compliance.rulesets import Ruleset


def detect(
    thread: list[dict[str, str]],
    ruleset: Ruleset,
    classifier: Optional[Callable[[list[dict[str, str]]], Optional[str]]] = None,
    timeout_seconds: float = 5.0,
) -> EscalationResult:
    """Detect escalation in a patient thread.

    Args:
        thread: List of message dicts with 'role' and 'text' keys.
        ruleset: The jurisdiction ruleset with escalation_routing.
        classifier: Optional classifier callable returning category or None.
        timeout_seconds: Timeout for classifier execution.

    Returns:
        EscalationResult with category, evidence, queue, target_response_minutes, clear, thread_sha256.

    Raises:
        NotImplementedError: Stub.
    """
    raise NotImplementedError("detect() not yet implemented")
