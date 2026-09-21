"""Graph fixtures for reachability tests."""

from typing import TypedDict

from langgraph.graph import StateGraph


class GraphState(TypedDict):
    """Simple state for test graphs."""

    value: int


def build_correct_graph() -> StateGraph[GraphState]:
    """Build a correctly wired escalation graph.

    Edges:
    - escalation_check -> escalate_to_clinician (conditional, label='escalate')
    - escalation_check -> draft (conditional, label='clear')
    - draft -> final
    - escalate_to_clinician -> final

    Only the 'clear' conditional edge can reach draft.

    Returns:
        Uncompiled StateGraph.
    """
    graph = StateGraph(GraphState)

    def check_node(state: GraphState) -> dict[str, int]:
        """Escalation check node."""
        return {"value": state["value"]}

    def draft_node(state: GraphState) -> dict[str, int]:
        """Draft node."""
        return {"value": state["value"]}

    def escalate_node(state: GraphState) -> dict[str, int]:
        """Escalate to clinician node."""
        return {"value": state["value"]}

    def final_node(state: GraphState) -> dict[str, int]:
        """Final node."""
        return {"value": state["value"]}

    graph.add_node("escalation_check", check_node)
    graph.add_node("draft", draft_node)
    graph.add_node("escalate_to_clinician", escalate_node)
    graph.add_node("final", final_node)

    # Correct routing: clear -> draft, escalate -> escalate_to_clinician
    graph.add_conditional_edges(
        "escalation_check",
        lambda state: "clear" if state["value"] == 0 else "escalate",
        {
            "clear": "draft",
            "escalate": "escalate_to_clinician",
        },
    )

    graph.add_edge("draft", "final")
    graph.add_edge("escalate_to_clinician", "final")

    graph.set_entry_point("escalation_check")
    graph.set_finish_point("final")

    return graph


def build_miswired_graph() -> StateGraph[GraphState]:
    """Build a deliberately mis-wired escalation graph.

    Has an unconditional edge directly from escalation_check to draft,
    bypassing the conditional edge check.

    Returns:
        Uncompiled StateGraph with a dangerous path.
    """
    graph = StateGraph(GraphState)

    def check_node(state: GraphState) -> dict[str, int]:
        """Escalation check node."""
        return {"value": state["value"]}

    def draft_node(state: GraphState) -> dict[str, int]:
        """Draft node."""
        return {"value": state["value"]}

    def escalate_node(state: GraphState) -> dict[str, int]:
        """Escalate to clinician node."""
        return {"value": state["value"]}

    def final_node(state: GraphState) -> dict[str, int]:
        """Final node."""
        return {"value": state["value"]}

    graph.add_node("escalation_check", check_node)
    graph.add_node("draft", draft_node)
    graph.add_node("escalate_to_clinician", escalate_node)
    graph.add_node("final", final_node)

    # DANGEROUS: unconditional edge directly to draft (wrong!)
    graph.add_edge("escalation_check", "draft")
    graph.add_edge("draft", "final")
    graph.add_edge("escalate_to_clinician", "final")

    graph.set_entry_point("escalation_check")
    graph.set_finish_point("final")

    return graph
