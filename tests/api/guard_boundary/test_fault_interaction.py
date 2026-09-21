"""Test AC5: guard runs before faults are injected."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from clinicloop.api.app import create_app
from clinicloop.evals.guard.corpus_loader import load_cases
from clinicloop.world.generator.snapshot import read_world_snapshot
from tests.api.guard_boundary.conftest import FaultInjectingMiddleware


@pytest.mark.parametrize("fault_mode", ["latency", "http_500", "http_429"])
def test_injected_faults_cannot_skip_the_guard(
    world_snapshot: Path,
    fault_mode: str,
) -> None:
    """Test that guard runs before faults are injected.

    AC5: With the fault-injecting ASGI middleware fixture owned by this
    issue that adds latency, a 500 response and a 429 response on /messages,
    a blocked message stores zero rows in all three fault modes, and the
    fixture's recorded call_order has "guard" at index 0 before the injected
    status is returned.

    Args:
        world_snapshot: Path to snapshot.
        fault_mode: The fault mode to test.
    """
    # Create a fresh app with the specified fault mode
    call_order: list[str] = []
    app = create_app(snapshot_path=world_snapshot)
    app.state.guard_trace = call_order

    # Add the fault-injecting middleware
    app.add_middleware(FaultInjectingMiddleware, mode=fault_mode, call_order=call_order)

    # Create a test client
    client = TestClient(app)

    snapshot = read_world_snapshot(world_snapshot)

    # Get a blocked case
    cases = load_cases()
    blocked_cases = [c for c in cases if c.expected_verdict == "block"]
    assert len(blocked_cases) > 0, "Need at least one blocked case"
    case = blocked_cases[0]

    # Construct body from case's assistant message texts
    body = " ".join(msg.text for msg in case.thread if msg.role == "assistant")

    # Get initial message count
    response = client.get("/messages")
    assert response.status_code == 200
    initial_count = len(response.json())

    # POST the blocked message
    payload = {
        "patient_id": snapshot.patients[0].patient_id,
        "channel": "chat",
        "body": body,
    }
    response = client.post("/messages", json=payload)

    # Verify message was not stored
    response = client.get("/messages")
    assert response.status_code == 200
    final_count = len(response.json())
    assert final_count == initial_count, (
        f"Fault mode {fault_mode}: blocked message was stored. "
        f"Count went from {initial_count} to {final_count}"
    )

    # Verify guard ran first in the call_order
    assert len(call_order) > 0, f"Fault mode {fault_mode}: call_order is empty"
    assert call_order[0] == "guard", (
        f"Fault mode {fault_mode}: expected 'guard' at index 0, got {call_order}"
    )
