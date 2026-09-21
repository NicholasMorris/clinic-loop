"""Reference graph demonstrating the approval gate pattern."""

from typing import Any, TypedDict


class ReferenceState(TypedDict):
    """State schema for the reference graph.

    Attributes:
        case_id: The case identifier (string).
        next: Tuple of next node names.
        decided_by: Who made the decision.
        decided_at: When the decision was made.
        outcome: The outcome of the decision (approved or rejected).
    """

    case_id: str
    next: tuple[str, ...] = ()
    decided_by: str = ""
    decided_at: str = ""
    outcome: str = ""


def build_reference_graph() -> Any:
    """Build the reference graph with approval gate pattern.

    Returns:
        A LangGraph StateGraph with typed state, approval gate,
        and two conditional edges for approve/reject decisions.
    """
    raise NotImplementedError("build_reference_graph not yet implemented")
