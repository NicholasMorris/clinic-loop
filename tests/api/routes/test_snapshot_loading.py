"""Tests for snapshot loading and schema version validation."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from clinicloop.api.app import SnapshotVersionUnsupported, create_app
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


def test_same_snapshot_same_body_and_version_is_checked(
    world_snapshot: Path,
) -> None:
    """Test that same snapshot returns identical bodies and version is checked.

    Acceptance criterion AC5: Two app instances created from the same snapshot
    return byte-identical GET /orders response bodies, and create_app against
    a snapshot file whose schema_version is "0" raises SnapshotVersionUnsupported
    naming both versions.
    """
    # Create two app instances from the same snapshot
    app1 = create_app(snapshot_path=world_snapshot)
    app2 = create_app(snapshot_path=world_snapshot)

    client1 = TestClient(app1)
    client2 = TestClient(app2)

    # Get orders from both clients
    response1 = client1.get("/orders")
    response2 = client2.get("/orders")

    assert response1.status_code == 200
    assert response2.status_code == 200

    # Compare byte-identical response bodies
    assert response1.content == response2.content

    # Test schema version check with unsupported version
    unsupported_snapshot = world_snapshot.parent / "unsupported_snapshot.json"
    snapshot_data = json.loads(world_snapshot.read_text())
    snapshot_data["schema_version"] = "0"
    unsupported_snapshot.write_text(json.dumps(snapshot_data))

    with pytest.raises(SnapshotVersionUnsupported) as exc_info:
        create_app(snapshot_path=unsupported_snapshot)

    # Check that the exception message names both versions
    error_msg = str(exc_info.value)
    assert "0" in error_msg
    assert "1" in error_msg
