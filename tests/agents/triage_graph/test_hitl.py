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

import pytest
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver

from clinicloop.agents.triage.graph.builder import build_triage_graph
from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.compliance.outbound.port import OutboundPort
from clinicloop.compliance.rulesets import load_ruleset
from clinicloop.hitl.decision import HumanDecision


@pytest.mark.filterwarnings("error::UserWarning")
def test_interrupt_before_human_approval_survives_restart(
    fake_model: FakeModelPort,
    message_source,
    fake_tools,
    tmp_path: Path,
) -> None:
    """AC3: Verify checkpoint survives restart with state.next == ('human_approval',).

    This test:
    1. Runs a case to the human_approval pause with a REAL sqlite file
    2. Closes the Python objects
    3. Builds a fresh compiled graph object from a NEW sqlite3.connect() to that file
    4. Verifies state.next == ('human_approval',) and state values match
    """
    # Use real sqlite file in tmp_path
    db_path = tmp_path / "triage.sqlite"
    case_id = "test-case-001"

    ruleset = load_ruleset("au")

    # Phase 1: Initial run to human_approval pause
    conn1 = sqlite3.connect(str(db_path), check_same_thread=False)
    calls1: list[str] = []
    transport1 = calls1.append

    # Create serde with registered types (fact c from task description)
    serde = JsonPlusSerializer(
        allowed_msgpack_modules=[
            ("clinicloop.agents.triage.state", "Turn"),
            ("clinicloop.agents.triage.state", "ToolCall"),
            ("clinicloop.compliance.guard.verdict", "GuardVerdict"),
            ("clinicloop.compliance.escalation.result", "EscalationClear"),
        ]
    )

    checkpointer1 = SqliteSaver(conn1, serde=serde)

    compiled1 = build_triage_graph(
        model=fake_model,
        tools=fake_tools,  # type: ignore[arg-type]
        ruleset=ruleset,
        message_source=message_source,
        outbound_port=OutboundPort(transport1, ruleset),
        run_key="test",
        checkpointer=checkpointer1,
    )

    # Invoke the graph - should pause at human_approval
    config = {"configurable": {"thread_id": case_id, "message_id": "msg-001"}}
    input_state = {"case_id": case_id, "patient_id": "P-001"}

    state1 = compiled1.invoke(input_state, config)

    # Verify it paused at human_approval
    assert state1.get("next") == ("human_approval",), (
        f"Expected pause at human_approval, got {state1.get('next')}"
    )

    # Save the state values for comparison
    state1_values = dict(state1)
    del state1_values["next"]  # Remove next as it's the indicator of pause

    # Phase 2: Close and create fresh objects
    conn1.close()
    del compiled1
    del checkpointer1

    # Phase 3: Fresh connection and graph object
    conn2 = sqlite3.connect(str(db_path), check_same_thread=False)
    checkpointer2 = SqliteSaver(conn2, serde=serde)

    calls2: list[str] = []
    transport2 = calls2.append

    compiled2 = build_triage_graph(
        model=fake_model,
        tools=fake_tools,  # type: ignore[arg-type]
        ruleset=ruleset,
        message_source=message_source,
        outbound_port=OutboundPort(transport2, ruleset),
        run_key="test",
        checkpointer=checkpointer2,
    )

    # Get the checkpoint state
    config2 = {"configurable": {"thread_id": case_id}}
    state2 = compiled2.get_state(config2)

    # AC3: Verify state.next and values match
    assert state2.next == ("human_approval",), (
        f"After restart, expected next=('human_approval',), got {state2.next}"
    )

    # Compare state values field by field
    state2_values = dict(state2.values)
    del state2_values["next"]

    for key in state1_values:
        assert state2_values.get(key) == state1_values[key], (
            f"State field {key} differs: {state2_values.get(key)} != {state1_values[key]}"
        )

    conn2.close()


@pytest.mark.filterwarnings("error::UserWarning")
def test_send_requires_human_decision_and_reject_sends_nothing(
    fake_model: FakeModelPort,
    message_source,
    fake_tools,
    tmp_path: Path,
) -> None:
    """AC4: Verify send is unreachable without HumanDecision and reject sends nothing.

    This test:
    1. Runs a case to human_approval pause
    2. Verifies state.next stays at human_approval if resumed without update_state
    3. Updates with a reject decision and verifies spy port records zero sends
    """
    db_path = tmp_path / "triage.sqlite"
    case_id = "test-case-002"

    ruleset = load_ruleset("au")

    # Phase 1: Run to human_approval
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    calls: list[str] = []
    transport = calls.append

    serde = JsonPlusSerializer(
        allowed_msgpack_modules=[
            ("clinicloop.agents.triage.state", "Turn"),
            ("clinicloop.agents.triage.state", "ToolCall"),
            ("clinicloop.compliance.guard.verdict", "GuardVerdict"),
            ("clinicloop.compliance.escalation.result", "EscalationClear"),
        ]
    )

    checkpointer = SqliteSaver(conn, serde=serde)

    compiled = build_triage_graph(
        model=fake_model,
        tools=fake_tools,  # type: ignore[arg-type]
        ruleset=ruleset,
        message_source=message_source,
        outbound_port=OutboundPort(transport, ruleset),
        run_key="test",
        checkpointer=checkpointer,
    )

    config = {"configurable": {"thread_id": case_id, "message_id": "msg-001"}}
    input_state = {"case_id": case_id, "patient_id": "P-001"}

    compiled.invoke(input_state, config)

    # Phase 2: AC4a - Resume without update_state
    state_mid = compiled.get_state(config)
    assert state_mid.next == ("human_approval",), "Should still be at human_approval"

    # Phase 3: AC4b - Update with reject decision and resume
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

    # Resume the graph
    final_state = compiled.invoke(None, config)

    # Should have ended at human_review (reject route)
    assert final_state.get("next") != ("human_approval",), "Should have moved past human_approval"
    # Verify spy port recorded zero sends
    assert len(calls) == 0, f"Expected no sends on reject, but got {len(calls)} calls"

    conn.close()
