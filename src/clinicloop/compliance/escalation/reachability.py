"""Reachability analysis for escalation graph paths."""

from typing import Any


def paths_from_escalation_to_draft(
    compiled_graph: Any,
    check_node: str = "escalation_check",
    draft_node: str = "draft",
    clear_label: str = "clear",
) -> list[tuple[str, str]]:
    """Find paths from escalation check edge to draft node.

    Validates that no unconditional edges from check_node reach draft_node,
    and no conditional edges with label != clear_label can reach draft_node.

    Args:
        compiled_graph: Compiled StateGraph from langgraph.
        check_node: Name of escalation check node.
        draft_node: Name of draft node.
        clear_label: Label of 'clear' conditional edges.

    Returns:
        List of (source, target) tuples representing problematic edges.
        Empty list means graph is wired correctly.
    """
    graph = compiled_graph.get_graph()
    violations: list[tuple[str, str]] = []

    # Get all edges from the graph
    edges = graph.edges

    # 1. Check for unconditional edges from check_node
    for edge in edges:
        source_node = edge.source
        target_node = edge.target
        is_conditional = edge.conditional

        # Check for unconditional edge from check_node
        if source_node == check_node and not is_conditional:
            # This is an unconditional edge; does it lead to draft?
            if target_node == draft_node:
                violations.append((source_node, target_node))
            else:
                # Check if target can reach draft via DFS
                if _can_reach(graph, target_node, draft_node):
                    violations.append((source_node, target_node))

    # 2. Check for conditional edges from check_node with label != clear_label
    for edge in edges:
        source_node = edge.source
        target_node = edge.target
        is_conditional = edge.conditional
        edge_data = edge.data

        if source_node == check_node and is_conditional:
            # Check the edge label
            label = edge_data if edge_data is not None else None

            # If label is not 'clear', check if target can reach draft
            if label != clear_label:
                if target_node == draft_node:
                    violations.append((source_node, target_node))
                elif _can_reach(graph, target_node, draft_node):
                    # Report the first edge on the path from target to draft
                    violations.append((source_node, target_node))

    return violations


def _can_reach(graph: Any, start_node: str, target_node: str) -> bool:
    """Check if start_node can reach target_node via DFS.

    Args:
        graph: CompiledStateGraph.get_graph() object.
        start_node: Starting node.
        target_node: Target node.

    Returns:
        True if target_node is reachable from start_node.
    """
    if start_node == target_node:
        return True

    visited: set[str] = set()
    stack: list[str] = [start_node]

    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)

        if current == target_node:
            return True

        # Get all edges from current node
        for edge in graph.edges:
            if edge.source == current:
                neighbor = edge.target
                if neighbor not in visited:
                    stack.append(neighbor)

    return False
