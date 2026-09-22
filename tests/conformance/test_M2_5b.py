"""Conformance tests for M2-5b issue #31.

Registers assertions for the requirement IDs: C1, L3, R1, R2.
"""

import sqlite3
from datetime import datetime
from typing import Any

import pytest
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver

from clinicloop.agents.triage.graph.builder import (
    TRIAGE_ALLOWED_MSGPACK_MODULES,
    build_triage_graph,
)
from clinicloop.agents.triage.graph.message_source import InMemoryMessageSource
from clinicloop.agents.triage.graph.state import GraphState
from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.compliance.escalation.reachability import paths_from_escalation_to_draft
from clinicloop.compliance.outbound.port import OutboundPort
from clinicloop.compliance.rulesets import load_ruleset
from clinicloop.hitl.decision import HumanDecision

SERDE = JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES)


class _InstantTools:
    def run(self, name: str, patient_id: str, order_id: str | None) -> str:
        return f"Order {order_id} status"


def _build(model: FakeModelPort, messages: dict[str, str]) -> tuple[Any, Any]:
    ruleset = load_ruleset("au")
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    spy: list[str] = []
    compiled = build_triage_graph(
        model=model,
        tools=_InstantTools(),
        ruleset=ruleset,
        message_source=InMemoryMessageSource(messages),
        outbound_port=OutboundPort(spy.append, ruleset),
        run_key="conformance",
        checkpointer=SqliteSaver(conn, serde=SERDE),
    )
    return compiled, spy


@pytest.mark.checklist_id("C1")
def test_c1_triage_agent_drafts_and_escalates() -> None:
    """C1: the graph drafts (approve path reaches send) and hard-escalates.

    A distress message never reaches draft, and a blocked draft cites its rule.
    """
    # A distress message escalates before any draft is produced.
    escalate_model = FakeModelPort(['{"intent": "mental_health_distress"}'])
    compiled, spy = _build(escalate_model, {"m": "I want to end my life."})
    final = compiled.invoke(
        {"case_id": "c1", "patient_id": "P-1"},
        {"configurable": {"thread_id": "c1", "message_id": "m"}},
    )
    assert final.get("escalation_category") == "distress"
    assert final.get("draft") is None
    assert compiled.get_state({"configurable": {"thread_id": "c1"}}).next == ()

    # A benign message drafts, is approved by a human, and is sent exactly once.
    draft_model = FakeModelPort(['{"intent": "general_question"}', "Yes, we ship internationally."])
    compiled2, spy2 = _build(draft_model, {"m2": "Do you ship internationally?"})
    cfg2 = {"configurable": {"thread_id": "c2", "message_id": "m2"}}
    compiled2.invoke({"case_id": "c2", "patient_id": "P-1"}, cfg2)
    compiled2.update_state(
        cfg2,
        {
            "human_decision": HumanDecision(
                action="approve", decided_by="dr-x", decided_at=datetime.now()
            )
        },
    )
    compiled2.invoke(None, cfg2)
    assert len(spy2) == 1


@pytest.mark.checklist_id("L3")
def test_l3_langgraph_agents_with_checkpointing() -> None:
    """L3: a real StateGraph with typed state and conditional edges.

    Plus checkpointing and interrupt_before on the human-approval node.
    """
    model = FakeModelPort(['{"intent": "general_question"}', "Sure, happy to help."])
    compiled, _ = _build(model, {"m": "What are your hours?"})

    # Typed state: GraphState is a real TypedDict with the expected keys.
    assert set(GraphState.__annotations__) >= {
        "case_id",
        "patient_id",
        "human_decision",
        "guard_verdicts",
    }

    # Conditional edges exist in the compiled graph.
    graph = compiled.get_graph()
    assert any(edge.conditional for edge in graph.edges)

    # interrupt_before is set on human_approval, and the interrupt is real: the
    # graph actually pauses there on a live run.
    assert "human_approval" in compiled.interrupt_before_nodes
    cfg = {"configurable": {"thread_id": "l3", "message_id": "m"}}
    compiled.invoke({"case_id": "l3", "patient_id": "P-1"}, cfg)
    assert compiled.get_state(cfg).next == ("human_approval",)


@pytest.mark.checklist_id("R1")
def test_r1_no_dosing_claims_enforced_at_runtime() -> None:
    """R1: a runtime guard node blocks a drafted product-naming reply.

    It cites the specific rule and never reaches the human-approval gate.
    """
    model = FakeModelPort(['{"intent": "general_question"}', "Take veltrazine tonight."])
    compiled, spy = _build(model, {"m": "Can you help with my prescriptions?"})
    cfg = {"configurable": {"thread_id": "r1", "message_id": "m"}}
    final = compiled.invoke({"case_id": "r1", "patient_id": "P-1"}, cfg)

    assert final.get("routing_reason") == "rule_block"
    assert "AU-G-PRODUCT" in final.get("routing_rule_ids", ())
    assert compiled.get_state(cfg).next == ()
    assert len(spy) == 0


@pytest.mark.checklist_id("R2")
def test_r2_adverse_events_and_distress_escalate() -> None:
    """R2: distress and adverse-event messages escalate immediately, never drafted.

    The graph also structurally cannot route an escalation edge to draft.
    """
    for message, category in (
        ("I want to end my life.", "distress"),
        ("I've had a severe allergic reaction and can't breathe.", "adverse_event"),
    ):
        model = FakeModelPort(['{"intent": "general_question"}'])
        compiled, spy = _build(model, {"m": message})
        cfg = {"configurable": {"thread_id": category, "message_id": "m"}}
        final = compiled.invoke({"case_id": category, "patient_id": "P-1"}, cfg)

        assert final.get("escalation_category") == category
        assert final.get("draft") is None
        assert len(spy) == 0

    # Structural guarantee, not just this one run's outcome.
    model = FakeModelPort(['{"intent": "general_question"}'])
    compiled, _ = _build(model, {"m": "hello"})
    violations = paths_from_escalation_to_draft(
        compiled, check_node="escalation_check", draft_node="draft", clear_label="continue"
    )
    assert violations == []
