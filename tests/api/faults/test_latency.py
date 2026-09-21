"""Tests for latency fault injection."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from clinicloop.api.app import create_app
from clinicloop.api.faults.middleware import attach_fault_middleware
from clinicloop.api.faults.profile import FaultProfile, LatencyRule, RouteFaultRules
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


class RecordingSleepFunction:
    """Callable that records sleep calls instead of actually sleeping."""

    def __init__(self) -> None:
        """Initialize the recording sleep function."""
        self.recorded_delays: list[float] = []

    def __call__(self, delay_seconds: float) -> None:
        """Record the delay without actually sleeping.

        Args:
            delay_seconds: Delay in seconds.
        """
        self.recorded_delays.append(delay_seconds)


def test_latency_rule_records_requested_delay_without_sleeping(
    world_snapshot: Path,
) -> None:
    """Test that latency rules record delays without real sleeping.

    Acceptance criterion AC2: With a profile whose GET /orders rule sets
    latency_ms=250 at probability 1.0 and a recording sleep callable injected,
    every fault log entry has fault_kind == "latency" and
    requested_delay_ms == 250, the recorder receives 0.25 seconds per request,
    and the response status stays 200.
    """
    # Create app without middleware first
    app = create_app(snapshot_path=world_snapshot)

    # Create a latency profile
    profile = FaultProfile(
        seed=42,
        routes={
            "GET /orders": RouteFaultRules(latency=LatencyRule(probability=1.0, latency_ms=250))
        },
    )

    # Create recording sleep function
    sleep_recorder = RecordingSleepFunction()

    # Attach middleware with recording sleep function
    middleware = attach_fault_middleware(app, profile, sleep_recorder)

    # Create client
    client = TestClient(app)

    # Make 10 requests to GET /orders
    for _ in range(10):
        response = client.get("/orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    # Check that all fault log entries are latency faults with correct delay
    fault_log = middleware.get_fault_log()
    assert len(fault_log) == 10
    for entry in fault_log:
        assert entry.get("fault_kind") == "latency"
        assert entry.get("requested_delay_ms") == 250

    # Check that sleep was called 10 times with 0.25 seconds each
    assert len(sleep_recorder.recorded_delays) == 10
    for delay in sleep_recorder.recorded_delays:
        assert delay == 0.25
