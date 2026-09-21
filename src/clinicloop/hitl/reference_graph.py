"""Reference graph demonstrating the approval gate pattern."""

from typing import Any, NotRequired, TypedDict

from langgraph.graph import StateGraph


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
    next: NotRequired[tuple[str, ...]]
    decided_by: NotRequired[str]
    decided_at: NotRequired[str]
    outcome: NotRequired[str]


def build_reference_graph() -> Any:
    """Build the reference graph with approval gate pattern.

    Returns:
        A LangGraph compiled graph with typed state, approval gate,
        and two conditional edges for approve/reject decisions.
    """
    graph: StateGraph[ReferenceState] = StateGraph(ReferenceState)

    # Add nodes
    def process_node(state: ReferenceState) -> ReferenceState:
        """Process the case."""
        return state

    def send_node(state: ReferenceState) -> ReferenceState:
        """Send the response."""
        return state

    def reject_node(state: ReferenceState) -> dict[str, Any]:
        """Reject the case."""
        return {"outcome": "rejected"}

    graph.add_node("process", process_node)
    graph.add_node("human_approval", lambda s: s)
    graph.add_node("send", send_node)
    graph.add_node("reject", reject_node)

    # Add edges
    graph.add_edge("process", "human_approval")

    # Add conditional edges from human_approval
    def route_decision(state: ReferenceState) -> str:
        """Route based on decision outcome."""
        outcome = state.get("outcome")
        if outcome == "approved":
            return "send"
        elif outcome == "rejected":
            return "reject"
        # Default to send if outcome is set to approved implicitly
        return "send"

    graph.add_conditional_edges(
        "human_approval",
        route_decision,
        {
            "send": "send",
            "reject": "reject",
        },
    )

    # Set entry point
    graph.set_entry_point("process")

    # Set finish points
    graph.set_finish_point("send")
    graph.set_finish_point("reject")

    # Compile with static interrupt_before
    compiled = graph.compile(interrupt_before=["human_approval"])

    return compiled
