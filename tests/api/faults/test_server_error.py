"""Tests for server error fault injection."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from clinicloop.api.app import create_app
from clinicloop.api.faults.middleware import attach_fault_middleware
from clinicloop.api.faults.profile import FaultProfile, RouteFaultRules, ServerErrorRule
from clinicloop.world.generator.snapshot import write_world_snapshot


@pytest.fixture
def world_snapshot(tmp_path: Path) -> Path:
    """Generate a test world snapshot.

    Args:
        tmp_path: Temporary directory fixture from pytest.

    Returns:
        Path to the written snapshot file.
    """
    from clinicloop.world.generator.build import generate_world

    world = generate_world(seed=42, population_size=5, span_days=30)
    snapshot_path = tmp_path / "test_snapshot.json"
    write_world_snapshot(world, snapshot_path)
    return snapshot_path


def test_error_rule_returns_configured_status(world_snapshot: Path) -> None:
    """Test that server error rules return configured status with fault_kind.

    Acceptance criterion AC3: With an error rule declaring status=503 at
    probability 1.0 for GET /orders, every request returns 503 and the response
    body contains fault_kind == "server_error"; the shipped demo profile
    declares that same 503 status.
    """
    # Create app without middleware first
    app = create_app(snapshot_path=world_snapshot)

    # Create a server error profile
    profile = FaultProfile(
        seed=42,
        routes={
            "GET /orders": RouteFaultRules(
                server_error=ServerErrorRule(probability=1.0, status=503)
            )
        },
    )

    # Attach middleware
    middleware = attach_fault_middleware(app, profile)

    # Create client
    client = TestClient(app)

    # Make 10 requests to GET /orders
    for _ in range(10):
        response = client.get("/orders")
        assert response.status_code == 503
        body = response.json()
        assert body.get("fault_kind") == "server_error"

    # Check that all fault log entries are server_error faults
    fault_log = middleware.get_fault_log()
    assert len(fault_log) == 10
    for entry in fault_log:
        assert entry.get("fault_kind") == "server_error"
