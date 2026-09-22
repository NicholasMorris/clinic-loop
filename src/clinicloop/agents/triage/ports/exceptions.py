"""Exceptions raised by TriageAgentPort."""


class HumanApprovalPending(RuntimeError):
    """The case reached human_approval and was auto-approved but resumption failed.

    This exception occurs when update_state/resume raises (e.g., a genuine
    ValueError from guard_final surfaces here).

    Attributes:
        case_id: The unique case identifier.
    """

    def __init__(self, case_id: str) -> None:
        """Initialize the exception.

        Args:
            case_id: The case identifier.
        """
        self.case_id = case_id
        super().__init__(f"Human approval pending failed to resume for case {case_id}")


class CaseEscalated(RuntimeError):
    """The graph ended at the 'escalate' terminal.

    The case requires human escalation and cannot be auto-resolved.

    Attributes:
        case_id: The unique case identifier.
    """

    def __init__(self, case_id: str) -> None:
        """Initialize the exception.

        Args:
            case_id: The case identifier.
        """
        self.case_id = case_id
        super().__init__(f"Case {case_id} escalated")

    def __str__(self) -> str:
        """Return string representation."""
        return f"Case {self.case_id} escalated"


class DraftNeedsHumanReview(RuntimeError):
    """The graph ended at the 'human_review' terminal.

    The draft is blocked by rules or requires human review for another reason.

    Attributes:
        case_id: The unique case identifier.
        routing_reason: The reason for blocking/routing (e.g., 'language', 'rule_block').
    """

    def __init__(self, case_id: str, routing_reason: str | None = None) -> None:
        """Initialize the exception.

        Args:
            case_id: The case identifier.
            routing_reason: The reason for blocking/routing.
        """
        self.case_id = case_id
        self.routing_reason = routing_reason
        if routing_reason:
            super().__init__(f"Case {case_id} needs human review: {routing_reason}")
        else:
            super().__init__(f"Case {case_id} needs human review")

    def __str__(self) -> str:
        """Return string representation."""
        if self.routing_reason:
            return f"Case {self.case_id} needs human review ({self.routing_reason})"
        return f"Case {self.case_id} needs human review"
