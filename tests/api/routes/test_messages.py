"""Tests for message endpoints: GET /messages, POST /messages."""

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


def test_post_message_returns_201_and_is_readable(
    client: TestClient,
    world_snapshot: Path,
) -> None:
    """Test POST /messages returns 201 and message is readable.

    Acceptance criterion AC3: POST /messages with a body satisfying
    MessageCreate returns 201 with a body containing the new message_id,
    and a subsequent GET /messages/{message_id} returns 200 with the same
    body content.
    """
    from clinicloop.world.generator.snapshot import read_world_snapshot

    snapshot = read_world_snapshot(world_snapshot)

    # Create a message
    payload = {
        "patient_id": snapshot.patients[0].patient_id,
        "channel": "chat",
        "body": "Test message body",
    }
    response = client.post("/messages", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert "message_id" in body
    message_id = body["message_id"]

    # Read the message back
    response = client.get(f"/messages/{message_id}")
    assert response.status_code == 200
    read_body = response.json()
    assert read_body["message_id"] == message_id
    assert read_body["patient_id"] == payload["patient_id"]
    assert read_body["channel"] == payload["channel"]
    assert read_body["body"] == payload["body"]


def test_missing_field_returns_422(
    client: TestClient,
) -> None:
    """Test POST /messages with missing field returns 422.

    Acceptance criterion AC4: POST /messages with a body missing the
    patient_id field returns 422 and the response body names patient_id
    in its error list.
    """
    # Missing patient_id
    payload = {
        "channel": "chat",
        "body": "Test message body",
    }
    response = client.post("/messages", json=payload)
    assert response.status_code == 422
    body = response.json()
    # FastAPI validation response includes "detail" key
    assert "detail" in body
    # Check that the error mentions patient_id
    detail_text = str(body)
    assert "patient_id" in detail_text
