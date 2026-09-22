"""Test HITL (human-in-the-loop) functionality: checkpointing and restart.

AC3: A case that reaches human_approval pauses before that node and persists a checkpoint;
a fresh graph object built in a new process against the same sqlite file and thread id
reports state.next == ("human_approval",) with state values equal field for field.

AC4: send is unreachable without a HumanDecision: resuming without update_state leaves
state.next == ("human_approval",), and a HumanDecision of reject terminates the run with
zero OutboundPort.send calls recorded by the spy port.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver

from clinicloop.agents.triage.graph.builder import (
    TRIAGE_ALLOWED_MSGPACK_MODULES,
    build_triage_graph,
)
from clinicloop.agents.triage.graph.message_source import InMemoryMessageSource
from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.compliance.outbound.port import OutboundPort
from clinicloop.compliance.rulesets import load_ruleset
from clinicloop.hitl.decision import HumanDecision

SERDE = JsonPlusSerializer(allowed_msgpack_modules=TRIAGE_ALLOWED_MSGPACK_MODULES)


class InstantToolRunner:
    """Returns a fixed summary immediately (unused for general_question, kept for parity)."""

    def run(self, name: str, patient_id: str, order_id: str | None) -> str:
        """Return a fixed summary."""
        return f"Order {order_id} is in transit"


def _build(db_path: Path, spy: list[str]) -> tuple[Any, Any]:
    """Build a graph for a general_question case (no tool call needed before the pause)."""
    message_source = InMemoryMessageSource({"msg-001": "Do you accept PayPal?"})
    model = FakeModelPort(
        ['{"intent": "general_question"}', "Yes, we accept PayPal for all orders."]
    )
    ruleset = load_ruleset("au")
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    compiled = build_triage_graph(
        model=model,
        tools=InstantToolRunner(),
        ruleset=ruleset,
        message_source=message_source,
        outbound_port=OutboundPort(spy.append, ruleset),
        run_key="test",
        checkpointer=SqliteSaver(conn, serde=SERDE),
    )
    return compiled, conn


def test_interrupt_before_human_approval_survives_restart(tmp_path: Path) -> None:
    """AC3: the checkpoint survives a real close-and-reopen of the sqlite connection."""
    db_path = tmp_path / "triage.sqlite"
    case_id = "test-case-001"
    config = {"configurable": {"thread_id": case_id, "message_id": "msg-001"}}

    # Phase 1: run to the human_approval pause with a REAL file (not :memory:).
    spy1: list[str] = []
    compiled1, conn1 = _build(db_path, spy1)
    compiled1.invoke({"case_id": case_id, "patient_id": "P-001"}, config)

    snap1 = compiled1.get_state(config)
    assert snap1.next == ("human_approval",)
    values1 = dict(snap1.values)

    # Phase 2: discard every Python object, close the connection.
    conn1.close()
    del compiled1

    # Phase 3: a completely fresh connection and compiled graph object.
    conn2 = sqlite3.connect(str(db_path), check_same_thread=False)
    ruleset = load_ruleset("au")
    spy2: list[str] = []
    compiled2 = build_triage_graph(
        model=FakeModelPort([]),
        tools=InstantToolRunner(),
        ruleset=ruleset,
        message_source=InMemoryMessageSource({}),
        outbound_port=OutboundPort(spy2.append, ruleset),
        run_key="test",
        checkpointer=SqliteSaver(conn2, serde=SERDE),
    )

    snap2 = compiled2.get_state({"configurable": {"thread_id": case_id}})
    assert snap2.next == ("human_approval",)

    assert set(snap2.values.keys()) == set(values1.keys())
    for key, value in values1.items():
        assert snap2.values[key] == value, f"field {key!r} differs after restart"

    conn2.close()


def test_send_requires_human_decision_and_reject_sends_nothing(tmp_path: Path) -> None:
    """AC4: no HumanDecision means no progress past the gate; reject sends nothing."""
    db_path = tmp_path / "triage.sqlite"
    case_id = "test-case-002"
    config = {"configurable": {"thread_id": case_id, "message_id": "msg-001"}}

    spy: list[str] = []
    compiled, conn = _build(db_path, spy)
    compiled.invoke({"case_id": case_id, "patient_id": "P-001"}, config)

    # AC4a: resuming with no update_state does not advance past the gate. The
    # routing function raises rather than silently defaulting to an outcome, and
    # the checkpoint left after the failed step still shows the pending pause.
    with pytest.raises(ValueError, match="human_decision"):
        compiled.invoke(None, config)
    assert compiled.get_state(config).next == ("human_approval",)
    assert len(spy) == 0

    # AC4b: a reject decision terminates the run with zero sends.
    compiled.update_state(
        config,
        {
            "human_decision": HumanDecision(
                action="reject",
                decided_by="clinician-001",
                decided_at=datetime.now(),
            )
        },
    )
    final = compiled.invoke(None, config)

    assert compiled.get_state(config).next == ()
    assert final.get("routing_reason") is None
    assert len(spy) == 0
    conn.close()
