"""Build the triage graph."""

import sqlite3
from typing import Any, Optional

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph

from clinicloop.agents.triage.graph.nodes import (
    escalate_node,
    human_approval_node,
    human_review_node,
    make_classify_intent_node,
    make_draft_node,
    make_escalation_check_node,
    make_guard_final_node,
    make_ingest_node,
    make_regulatory_guard_node,
    make_resolve_node,
    make_send_node,
)
from clinicloop.agents.triage.graph.state import GraphState
from clinicloop.hitl.checkpoint import checkpoint_root


def build_triage_graph(
    *,
    model: Any,
    tools: Any,
    ruleset: Any,
    message_source: Any,
    outbound_port: Any,
    classifier: Optional[Any] = None,
    run_key: str = "triage",
    timeout_seconds: float = 5.0,
    checkpointer: Optional[Any] = None,
) -> Any:
    """Build and compile the triage LangGraph.

    Args:
        model: ModelPort with complete() method.
        tools: ToolRunner protocol.
        ruleset: Ruleset object.
        message_source: MessageSource implementation.
        outbound_port: OutboundPort implementation.
        classifier: Optional escalation classifier.
        run_key: Key for consistent hashing.
        timeout_seconds: Timeout for tool execution.
        checkpointer: Optional SqliteSaver for checkpointing.

    Returns:
        A compiled LangGraph StateGraph with interrupt_before=['human_approval'].
    """
    # Create the state graph
    graph: StateGraph = StateGraph(GraphState)

    # Add all nodes
    graph.add_node("ingest", make_ingest_node(message_source, run_key))
    graph.add_node("classify_intent", make_classify_intent_node(model))
    graph.add_node("escalation_check", make_escalation_check_node(ruleset, classifier=classifier))
    graph.add_node("resolve", make_resolve_node(model, tools, timeout_seconds=timeout_seconds))
    graph.add_node("draft", make_draft_node(model))
    graph.add_node("regulatory_guard", make_regulatory_guard_node(ruleset))
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("guard_final", make_guard_final_node(ruleset))
    graph.add_node("send", make_send_node(outbound_port))
    graph.add_node("human_review", human_review_node)
    graph.add_node("escalate", escalate_node)

    # Add unconditional edges
    graph.add_edge("ingest", "classify_intent")
    graph.add_edge("classify_intent", "escalation_check")

    # Conditional edge from escalation_check: continue (no escalation) or escalate
    def route_escalation_check(state: GraphState) -> str:
        """Route based on escalation result."""
        category = state.get("escalation_category")
        if category in (None, "none"):
            return "continue"
        else:
            return "escalate"

    graph.add_conditional_edges(
        "escalation_check",
        route_escalation_check,
        {
            "continue": "resolve",
            "escalate": "escalate",
        },
    )

    # Conditional edge from resolve: timeout or ok
    def route_resolve(state: GraphState) -> str:
        """Route based on resolve result."""
        if state.get("routing_reason") == "tool_timeout":
            return "timeout"
        return "ok"

    graph.add_conditional_edges(
        "resolve",
        route_resolve,
        {
            "ok": "draft",
            "timeout": "escalate",
        },
    )

    # Conditional edge from draft: language or ok
    def route_draft(state: GraphState) -> str:
        """Route based on draft result."""
        if state.get("routing_reason") == "language":
            return "language"
        return "ok"

    graph.add_conditional_edges(
        "draft",
        route_draft,
        {
            "ok": "regulatory_guard",
            "language": "human_review",
        },
    )

    # Conditional edge from regulatory_guard: blocked or ok
    def route_regulatory_guard(state: GraphState) -> str:
        """Route based on regulatory guard result."""
        if state.get("routing_reason") == "rule_block":
            return "blocked"
        return "ok"

    graph.add_conditional_edges(
        "regulatory_guard",
        route_regulatory_guard,
        {
            "ok": "human_approval",
            "blocked": "human_review",
        },
    )

    # Conditional edge from human_approval: approve, edit, or reject
    def route_human_decision(state: GraphState) -> str:
        """Route based on human decision."""
        decision = state.get("human_decision")
        if decision:
            return decision.action
        # Should not happen in normal flow
        return "approve"

    graph.add_conditional_edges(
        "human_approval",
        route_human_decision,
        {
            "approve": "guard_final",
            "edit": "guard_final",
            "reject": "human_review",
        },
    )

    # Conditional edge from guard_final: blocked or ok
    def route_guard_final(state: GraphState) -> str:
        """Route based on final guard result."""
        if state.get("routing_reason") == "rule_block":
            return "blocked"
        return "ok"

    graph.add_conditional_edges(
        "guard_final",
        route_guard_final,
        {
            "ok": "send",
            "blocked": "human_review",
        },
    )

    # Set entry point
    graph.set_entry_point("ingest")

    # Set finish points
    graph.set_finish_point("send")
    graph.set_finish_point("human_review")
    graph.set_finish_point("escalate")

    # Build checkpointer if not provided
    if checkpointer is None:
        checkpoint_db = checkpoint_root() / "triage.sqlite"
        checkpoint_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(checkpoint_db), check_same_thread=False)
        serde = JsonPlusSerializer(
            allowed_msgpack_modules=[
                ("clinicloop.agents.triage.state", "Turn"),
                ("clinicloop.agents.triage.state", "ToolCall"),
                ("clinicloop.compliance.guard.verdict", "GuardVerdict"),
                ("clinicloop.compliance.escalation.result", "EscalationClear"),
            ]
        )
        checkpointer = SqliteSaver(conn, serde=serde)

    # Compile with interrupt_before
    compiled = graph.compile(interrupt_before=["human_approval"], checkpointer=checkpointer)

    return compiled
