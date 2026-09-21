"""Test reachability analysis for escalation graphs."""

import pytest

from clinicloop.compliance.escalation.reachability import paths_from_escalation_to_draft
from tests.compliance.escalation.fixtures.graphs import (
    build_correct_graph,
    build_miswired_graph,
)


def test_no_path_from_escalation_edge_to_draft():
    """AC5: Reachability returns empty list for correct graph.

    For a mis-wired graph with an unconditional edge from escalation_check
    to draft, returns [(escalation_check, draft)].
    """
    # Test correct graph
    correct = build_correct_graph()
    compiled_correct = correct.compile()
    paths = paths_from_escalation_to_draft(compiled_correct)
    assert paths == [], f"Correct graph should have no paths, got {paths}"

    # Test mis-wired graph
    miswired = build_miswired_graph()
    compiled_miswired = miswired.compile()
    paths = paths_from_escalation_to_draft(compiled_miswired)
    assert len(paths) == 1, f"Mis-wired graph should have 1 path, got {len(paths)}"
    assert paths[0] == (
        "escalation_check",
        "draft",
    ), f"Path should be (escalation_check, draft), got {paths[0]}"


def test_reachability_with_two_hop_path():
    """Additional test: A path that reaches draft via another node."""
    # Create a graph where escalate_to_clinician -> draft (wrong!)
    from langgraph.graph import StateGraph
    from typing import TypedDict

    class GraphState(TypedDict):
        value: int

    graph = StateGraph(GraphState)

    def check_node(state: GraphState) -> dict[str, int]:
        return {"value": state["value"]}

    def draft_node(state: GraphState) -> dict[str, int]:
        return {"value": state["value"]}

    def escalate_node(state: GraphState) -> dict[str, int]:
        return {"value": state["value"]}

    def final_node(state: GraphState) -> dict[str, int]:
        return {"value": state["value"]}

    graph.add_node("escalation_check", check_node)
    graph.add_node("draft", draft_node)
    graph.add_node("escalate_to_clinician", escalate_node)
    graph.add_node("final", final_node)

    # Correct edges for escalation
    graph.add_conditional_edges(
        "escalation_check",
        lambda state: "clear" if state["value"] == 0 else "escalate",
        {
            "clear": "draft",
            "escalate": "escalate_to_clinician",
        },
    )

    # WRONG: escalate_to_clinician can reach draft
    graph.add_edge("escalate_to_clinician", "draft")
    graph.add_edge("draft", "final")

    graph.set_entry_point("escalation_check")
    graph.set_finish_point("final")

    compiled = graph.compile()
    paths = paths_from_escalation_to_draft(compiled)
    # Should report the edge from escalate_to_clinician to draft
    assert len(paths) > 0, "Should detect path from escalate_to_clinician to draft"
