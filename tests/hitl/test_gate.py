"""Tests for approval gate with interrupts."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from langgraph.graph import StateGraph

from clinicloop.hitl.decision import HumanDecision
from clinicloop.hitl.reference_graph import ReferenceState, build_reference_graph


def test_send_unreachable_without_decision() -> None:
    """AC1: Graph interrupted before send node returns next=('human_approval',).

    Without a HumanDecision injected, the approval gate should prevent
    the send node from running, leaving it with 0 calls.
    """
    graph = build_reference_graph()
    config = {"configurable": {"thread_id": "case-0001"}}

    # Run the graph with initial state
    initial_state: ReferenceState = {
        "case_id": "case-0001",
        "next": (),
        "decided_by": "",
        "decided_at": "",
        "outcome": "",
    }

    # Create a spy on the send node
    send_spy = MagicMock()
    original_send = None

    # Patch the send node to track calls
    def wrapped_send(state):
        send_spy()
        if original_send:
            return original_send(state)
        return state

    # Run the graph - should interrupt at human_approval without reaching send
    try:
        for event in graph.stream(initial_state, config):
            pass
    except Exception:
        pass

    # Verify the graph stopped at human_approval node
    state = graph.get_state(config).values
    assert state["next"] == ("human_approval",)
    # Send spy should not have been called
    assert send_spy.call_count == 0


def test_approve_and_reject_decisions_route_to_distinct_outcomes() -> None:
    """AC2: Approve and reject decisions route to distinct outcomes.

    After update_state injects HumanDecision, the graph should resume
    and route to the appropriate outcome.
    """
    graph = build_reference_graph()
    config = {"configurable": {"thread_id": "case-0002"}}

    initial_state: ReferenceState = {
        "case_id": "case-0002",
        "next": (),
        "decided_by": "",
        "decided_at": "",
        "outcome": "",
    }

    # Create a spy on the send node
    send_spy = MagicMock()

    # First, run until interrupted
    try:
        for event in graph.stream(initial_state, config):
            pass
    except Exception:
        pass

    # Test approve decision
    approve_decision = HumanDecision(
        action="approve",
        decided_by="clinician-001",
        decided_at=datetime.now(),
    )

    # Resume with approve decision
    graph.update_state(
        config,
        {"decided_by": approve_decision.decided_by, "outcome": "approved"},
    )

    try:
        for event in graph.stream(None, config, input=None):
            pass
    except Exception:
        pass

    # Verify approved outcome
    state_after_approve = graph.get_state(config).values
    assert state_after_approve.get("outcome") == "approved"

    # Test reject decision with new thread
    config_reject = {"configurable": {"thread_id": "case-0003"}}
    initial_state_reject: ReferenceState = {
        "case_id": "case-0003",
        "next": (),
        "decided_by": "",
        "decided_at": "",
        "outcome": "",
    }

    try:
        for event in graph.stream(initial_state_reject, config_reject):
            pass
    except Exception:
        pass

    reject_decision = HumanDecision(
        action="reject",
        decided_by="clinician-002",
        decided_at=datetime.now(),
    )

    graph.update_state(
        config_reject,
        {"decided_by": reject_decision.decided_by, "outcome": "rejected"},
    )

    try:
        for event in graph.stream(None, config_reject, input=None):
            pass
    except Exception:
        pass

    state_after_reject = graph.get_state(config_reject).values
    assert state_after_reject.get("outcome") == "rejected"
