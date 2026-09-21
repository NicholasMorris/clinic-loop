"""Tests for OpenAPI schema."""

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


def test_openapi_lists_four_resource_paths(client: TestClient) -> None:
    """Test that OpenAPI document lists the four resource paths.

    Acceptance criterion AC6: GET /openapi.json returns 200 and its paths
    object contains /patients, /orders, /consults and /messages.
    """
    response = client.get("/openapi.json")
    assert response.status_code == 200

    document = response.json()
    assert "paths" in document

    paths = document["paths"]
    required_paths = ["/patients", "/orders", "/consults", "/messages"]
    for path in required_paths:
        assert path in paths, f"Missing path: {path}"
