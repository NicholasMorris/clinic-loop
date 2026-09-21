"""Tests for loopback-only binding."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from clinicloop.api.app import create_app
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


@pytest.fixture
def client(world_snapshot: Path) -> TestClient:
    """Create a FastAPI test client with a loaded snapshot.

    Args:
        world_snapshot: Path to the snapshot file.

    Returns:
        A TestClient for the app.
    """
    app = create_app(snapshot_path=world_snapshot)
    return TestClient(app)


def test_non_loopback_bind_is_rejected(world_snapshot: Path) -> None:
    """Test that binding to non-loopback hosts raises ValueError.

    Acceptance criterion AC7: The API test module passes under pytest-socket
    with only loopback allowed, and an attempt to bind the app to a non-loopback
    host raises ValueError naming the rejected host.
    """
    # Test that non-loopback host raises ValueError
    with pytest.raises(ValueError) as exc_info:
        create_app(snapshot_path=world_snapshot, host="0.0.0.0")

    error_msg = str(exc_info.value)
    assert "0.0.0.0" in error_msg


def test_api_works_under_loopback_only(client: TestClient) -> None:
    """Test that API works when run under loopback-only socket policy.

    This test verifies that the API can operate successfully when
    pytest-socket restricts connections to loopback only.
    """
    # This test simply exercises the client under pytest-socket restrictions
    response = client.get("/patients")
    assert response.status_code == 200
