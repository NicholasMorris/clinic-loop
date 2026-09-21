"""Test AC5: guard runs before faults are injected."""

import pytest
from fastapi.testclient import TestClient
from starlette.testclient import TestClient as BaseTestClient

from clinicloop.evals.guard.corpus_loader import load_cases
from clinicloop.world.generator.snapshot import read_world_snapshot
from tests.api.guard_boundary.conftest import FaultInjectingMiddleware


@pytest.fixture
def fault_modes() -> list[str]:
    """Return the fault modes to test.

    Returns:
        List of fault mode strings.
    """
    return ["latency", "http_500", "http_429"]


def test_injected_faults_cannot_skip_the_guard(
    app,
    world_snapshot,
    fault_modes,
) -> None:
    """Test that guard runs before faults are injected.

    AC5: With the fault-injecting ASGI middleware fixture owned by this
    issue that adds latency, a 500 response and a 429 response on /messages,
    a blocked message stores zero rows in all three fault modes, and the
    fixture's recorded call_order has "guard" at index 0 before the injected
    status is returned.

    Args:
        app: The FastAPI app fixture.
        world_snapshot: Path to snapshot.
        fault_modes: List of fault modes to test.
    """
    snapshot = read_world_snapshot(world_snapshot)

    # Get a blocked case
    cases = load_cases()
    blocked_cases = [c for c in cases if c.expected_verdict == "block"]
    assert len(blocked_cases) > 0, "Need at least one blocked case"
    case = blocked_cases[0]

    # Construct body from case's assistant message texts
    body = " ".join(msg.text for msg in case.thread if msg.role == "assistant")

    for fault_mode in fault_modes:
        # Reset app state
        app.state.created_messages = {}
        app.state.message_counter = len(snapshot.messages)
        call_order: list[str] = []
        app.state.guard_trace = call_order

        # Create middleware and client
        from starlette.middleware.base import BaseHTTPMiddleware

        middleware_app = FaultInjectingMiddleware(app, fault_mode, call_order)

        # Stack the middleware on app
        middleware_app = BaseHTTPMiddleware(app, dispatch=middleware_app.dispatch)

        client = TestClient(app)

        # Add the middleware to the app
        app.add_middleware(FaultInjectingMiddleware, mode=fault_mode, call_order=call_order)

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

        # Verify guard ran first
        assert len(call_order) > 0, f"Fault mode {fault_mode}: call_order is empty"
        assert call_order[0] == "guard", (
            f"Fault mode {fault_mode}: expected 'guard' at index 0, got {call_order}"
        )
