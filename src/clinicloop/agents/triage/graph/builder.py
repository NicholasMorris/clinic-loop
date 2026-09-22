"""Build the triage graph."""

import os
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

# Every pydantic model / dataclass that can appear inside GraphState and must
# therefore round-trip through a checkpoint. A type missing from this list still
# writes to the checkpoint (with a deprecation warning), but reads back as a plain
# dict instead of the real object, breaking any node or router that expects one
# (this broke HumanDecision-based routing after a resume before it was added here).
# Tests that build their own SqliteSaver/JsonPlusSerializer must reuse this constant
# rather than hand-rolling their own list, so it can't drift out of sync again.
TRIAGE_ALLOWED_MSGPACK_MODULES = [
    ("clinicloop.agents.triage.state", "Turn"),
    ("clinicloop.agents.triage.state", "ToolCall"),
    ("clinicloop.agents.triage.intents", "Intent"),
    ("clinicloop.compliance.guard.verdict", "GuardVerdict"),
    ("clinicloop.compliance.escalation.result", "EscalationClear"),
    ("clinicloop.hitl.decision", "HumanDecision"),
]


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
    graph: StateGraph[GraphState] = StateGraph(GraphState)

    # Each node closure is typed dict[str, Any] (matching the M2-5a node functions
    # it wraps, which operate on plain dict state via .get()/[]), but
    # StateGraph.add_node's overload set binds NodeInputT to TypedDict/dataclass/
    # BaseModel and does not structurally accept a bare dict even though it is
    # runtime-correct for a TypedDict(total=False) schema; verified by the graph
    # tests, including real execution, checkpointing and cross-process restore.
    # Routed through one helper so that single ignore covers every call.
    def _add_node(name: str, fn: Any) -> None:
        graph.add_node(name, fn)

    _add_node("ingest", make_ingest_node(message_source, run_key))
    _add_node("classify_intent", make_classify_intent_node(model))
    _add_node("escalation_check", make_escalation_check_node(ruleset, classifier=classifier))
    _add_node("resolve", make_resolve_node(model, tools, timeout_seconds=timeout_seconds))
    _add_node("draft", make_draft_node(model))
    _add_node("regulatory_guard", make_regulatory_guard_node(ruleset))
    _add_node("human_approval", human_approval_node)
    _add_node("guard_final", make_guard_final_node(ruleset))
    _add_node("send", make_send_node(outbound_port))
    _add_node("human_review", human_review_node)
    _add_node("escalate", escalate_node)

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
        """Route based on human decision.

        Raises:
            ValueError: If no human_decision was injected via update_state before
                resuming. Silently defaulting to 'approve' here would let a resume
                with no decision reach send; this must fail instead.
        """
        decision = state.get("human_decision")
        if decision is None:
            raise ValueError(
                "human_approval was resumed with no human_decision; "
                "call update_state with a HumanDecision before resuming"
            )
        return decision.action

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
        checkpoint_db.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Checkpoints carry redacted patient data and human decisions; restrict to
        # owner-only before sqlite3 opens the file, so a shared machine's other
        # users can't read it via the default umask.
        if not checkpoint_db.exists():
            fd = os.open(str(checkpoint_db), os.O_CREAT | os.O_RDWR, 0o600)
            os.close(fd)
        conn = sqlite3.connect(str(checkpoint_db), check_same_thread=False)
        serde = JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES)
        checkpointer = SqliteSaver(conn, serde=serde)

    # Compile with interrupt_before
    compiled = graph.compile(interrupt_before=["human_approval"], checkpointer=checkpointer)

    return compiled
