"""Tests for read endpoints: GET /patients, /orders, /consults, /messages."""

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


def test_collection_and_item_reads_return_200(
    client: TestClient,
    world_snapshot: Path,
) -> None:
    """Test that collection and item endpoints return 200 with correct data.

    Acceptance criterion AC1: GET /patients, /orders, /consults, /messages
    each return 200 with a JSON array whose length matches the snapshot count,
    and GET /patients/{id} returns 200 with a PatientRead schema.
    """
    from clinicloop.world.generator.snapshot import read_world_snapshot

    snapshot = read_world_snapshot(world_snapshot)

    # Test /patients collection
    response = client.get("/patients")
    assert response.status_code == 200
    patients = response.json()
    assert isinstance(patients, list)
    assert len(patients) == len(snapshot.patients)

    # Test /orders collection
    response = client.get("/orders")
    assert response.status_code == 200
    orders = response.json()
    assert isinstance(orders, list)
    assert len(orders) == len(snapshot.orders)

    # Test /consults collection
    response = client.get("/consults")
    assert response.status_code == 200
    consults = response.json()
    assert isinstance(consults, list)
    assert len(consults) == len(snapshot.consults)

    # Test /messages collection
    response = client.get("/messages")
    assert response.status_code == 200
    messages = response.json()
    assert isinstance(messages, list)
    assert len(messages) == len(snapshot.messages)

    # Test /patients/{id} with a valid id
    if snapshot.patients:
        patient_id = snapshot.patients[0].patient_id
        response = client.get(f"/patients/{patient_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["patient_id"] == patient_id


def test_unknown_identifier_returns_404_with_detail(
    client: TestClient,
) -> None:
    """Test that unknown identifiers return 404 with detail string.

    Acceptance criterion AC2: GET /patients/{id}, GET /orders/{id},
    GET /consults/{id} with an absent identifier return 404 with a detail
    string that includes the requested identifier.
    """
    # Test unknown patient
    response = client.get("/patients/P999999")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    assert "P999999" in body["detail"]

    # Test unknown order
    response = client.get("/orders/O999999")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    assert "O999999" in body["detail"]

    # Test unknown consult
    response = client.get("/consults/C999999")
    assert response.status_code == 404
    body = response.json()
    assert "detail" in body
    assert "C999999" in body["detail"]
