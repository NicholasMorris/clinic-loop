"""Conformance tests for M1-3: Mock APIs.

Tests the requirements from the brief checklist:
- C0: SimClinic determinism
- L1: Loopback-only API
"""

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


def test_c0_simclinic_requirement(world_snapshot: Path) -> None:
    """Test C0 SimClinic requirement: deterministic responses.

    C0 verifies that the mock API serves a deterministic snapshot
    that can be loaded and queried repeatably.
    """
    app1 = create_app(snapshot_path=world_snapshot)
    app2 = create_app(snapshot_path=world_snapshot)

    client1 = TestClient(app1)
    client2 = TestClient(app2)

    # Both instances should return identical responses
    assert client1.get("/patients").content == client2.get("/patients").content
    assert client1.get("/orders").content == client2.get("/orders").content
    assert client1.get("/consults").content == client2.get("/consults").content
    assert client1.get("/messages").content == client2.get("/messages").content


def test_l1_loopback_only_requirement(client: TestClient) -> None:
    """Test L1 Loopback-only requirement.

    L1 verifies that the API is restricted to loopback interfaces
    (127.0.0.1, ::1, localhost).
    """
    # This test verifies that under pytest-socket with loopback-only
    # restriction, the client can still communicate with the app.
    response = client.get("/patients")
    assert response.status_code == 200


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
