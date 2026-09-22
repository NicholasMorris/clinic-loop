"""Test that escalation routes cannot reach draft.

AC2: The M2-3 reachability helper called on the compiled graph returns an empty path list
for every edge leaving escalation_check to escalate, so no path reaches draft from an
escalation edge.
"""

import sqlite3
from typing import Any

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from clinicloop.agents.triage.graph.builder import (
    TRIAGE_ALLOWED_MSGPACK_MODULES,
    build_triage_graph,
)
from clinicloop.agents.triage.graph.message_source import InMemoryMessageSource
from clinicloop.agents.triage.graph.state import GraphState
from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.agents.triage.tools import ToolRunner
from clinicloop.compliance.escalation.reachability import paths_from_escalation_to_draft
from clinicloop.compliance.outbound.port import OutboundPort
from clinicloop.compliance.rulesets import load_ruleset

SERDE = JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES)


def test_no_path_from_escalation_edge_to_draft(
    fake_model: FakeModelPort,
    message_source: InMemoryMessageSource,
    fake_tools: ToolRunner,
) -> None:
    """The real, correctly wired triage graph has no escalation-to-draft path."""
    calls: list[str] = []
    ruleset = load_ruleset("au")
    conn = sqlite3.connect(":memory:", check_same_thread=False)

    compiled = build_triage_graph(
        model=fake_model,
        tools=fake_tools,
        ruleset=ruleset,
        message_source=message_source,
        outbound_port=OutboundPort(calls.append, ruleset),
        run_key="test",
        checkpointer=SqliteSaver(conn, serde=SERDE),
    )

    violations = paths_from_escalation_to_draft(
        compiled, check_node="escalation_check", draft_node="draft", clear_label="continue"
    )
    assert violations == [], f"Escalation edge reaches draft via: {violations}"


def test_a_deliberately_miswired_graph_is_caught() -> None:
    """The helper actually detects a regression: escalation_check wired straight to draft."""

    def noop(state: GraphState) -> dict[str, Any]:
        return {}

    graph: StateGraph[GraphState] = StateGraph(GraphState)
    for name in ("ingest", "escalation_check", "draft"):
        graph.add_node(name, noop)
    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "escalation_check")
    # Mis-wired: unconditional edge straight to draft, skipping the escalate branch.
    graph.add_edge("escalation_check", "draft")
    graph.add_edge("draft", END)
    compiled = graph.compile()

    violations = paths_from_escalation_to_draft(
        compiled, check_node="escalation_check", draft_node="draft", clear_label="continue"
    )
    assert violations == [("escalation_check", "draft")]
