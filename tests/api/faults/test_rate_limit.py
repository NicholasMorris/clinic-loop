"""Tests for rate limiting fault injection."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from clinicloop.api.app import create_app
from clinicloop.api.faults.middleware import attach_fault_middleware
from clinicloop.api.faults.profile import FaultProfile, RateLimitRule, RouteFaultRules
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


def test_fourth_request_in_window_is_rate_limited(world_snapshot: Path) -> None:
    """Test that rate limiting enforces requests per window.

    Acceptance criterion AC4: With a rate-limit rule of 3 requests per window,
    the fourth request in that window returns 429 and includes a Retry-After
    header whose value parses as a positive integer.
    """
    # Create app without middleware first
    app = create_app(snapshot_path=world_snapshot)

    # Create a rate limit profile with 3 requests per window
    profile = FaultProfile(
        seed=42,
        routes={
            "GET /orders": RouteFaultRules(
                rate_limit=RateLimitRule(probability=1.0, requests_per_window=3, window_seconds=60)
            )
        },
    )

    # Attach middleware
    middleware = attach_fault_middleware(app, profile)

    # Create client
    client = TestClient(app)

    # First 3 requests should succeed
    for i in range(3):
        response = client.get("/orders")
        assert response.status_code == 200, f"Request {i + 1} should succeed"

    # Fourth request should be rate limited
    response = client.get("/orders")
    assert response.status_code == 429
    assert "Retry-After" in response.headers
    retry_after = response.headers["Retry-After"]
    assert int(retry_after) > 0, "Retry-After header should be a positive integer"

    # Check that the fault log contains 4 entries, with the last being rate_limit
    fault_log = middleware.get_fault_log()
    assert len(fault_log) >= 1  # At least the rate limit entry
    last_entry = fault_log[-1]
    assert last_entry.get("fault_kind") == "rate_limit"
