"""Escalation detection for adverse events, misuse, distress, pregnancy, and clinical advice."""

from clinicloop.compliance.escalation.result import (
    EscalationClear,
    EscalationClearForbidden,
    EscalationRequired,
    EscalationResult,
    EvidenceSpan,
)

__all__ = [
    "EscalationClear",
    "EscalationClearForbidden",
    "EscalationRequired",
    "EscalationResult",
    "EvidenceSpan",
]
