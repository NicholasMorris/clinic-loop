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


def test_post_twice_gives_distinct_ids_no_collision(
    client: TestClient,
    world_snapshot: Path,
) -> None:
    """Test that posting twice gives two distinct IDs that don't collide with world IDs.

    This tests that:
    1. Two posted messages get different IDs
    2. The IDs do not collide with any world message IDs
    """
    from clinicloop.world.generator.snapshot import read_world_snapshot

    snapshot = read_world_snapshot(world_snapshot)

    # Find the highest message ID in the world
    if snapshot.messages:
        # Extract numbers from message IDs like "M000001"
        max_id = max(
            int(m.message_id[1:]) for m in snapshot.messages
        )
    else:
        max_id = 0

    # Create two messages
    payload1 = {
        "patient_id": snapshot.patients[0].patient_id,
        "channel": "chat",
        "body": "First message",
    }
    response1 = client.post("/messages", json=payload1)
    assert response1.status_code == 201
    message_id_1 = response1.json()["message_id"]

    payload2 = {
        "patient_id": snapshot.patients[0].patient_id,
        "channel": "email",
        "body": "Second message",
    }
    response2 = client.post("/messages", json=payload2)
    assert response2.status_code == 201
    message_id_2 = response2.json()["message_id"]

    # Verify IDs are different
    assert message_id_1 != message_id_2

    # Verify IDs don't collide with world IDs
    world_ids = {m.message_id for m in snapshot.messages}
    assert message_id_1 not in world_ids
    assert message_id_2 not in world_ids

    # Verify IDs are after the highest world ID
    id_num_1 = int(message_id_1[1:])
    id_num_2 = int(message_id_2[1:])
    assert id_num_1 > max_id
    assert id_num_2 > max_id


def test_posted_message_appears_in_get_messages(
    client: TestClient,
    world_snapshot: Path,
) -> None:
    """Test that posted messages appear in GET /messages.

    This tests that GET /messages includes both world messages and newly posted
    messages.
    """
    from clinicloop.world.generator.snapshot import read_world_snapshot

    snapshot = read_world_snapshot(world_snapshot)

    # Get initial count
    response = client.get("/messages")
    assert response.status_code == 200
    initial_count = len(response.json())

    # Create a message
    payload = {
        "patient_id": snapshot.patients[0].patient_id,
        "channel": "chat",
        "body": "Test message for list",
    }
    response = client.post("/messages", json=payload)
    assert response.status_code == 201
    message_id = response.json()["message_id"]

    # Get all messages and check the count increased
    response = client.get("/messages")
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == initial_count + 1

    # Verify the new message is in the list
    message_ids = [m["message_id"] for m in messages]
    assert message_id in message_ids


def test_second_app_instance_does_not_see_posted_message(
    world_snapshot: Path,
) -> None:
    """Test that a second app instance created from the same snapshot doesn't see posted messages.

    This verifies that message creation is per-instance and doesn't persist to the snapshot.
    """
    from clinicloop.world.generator.snapshot import read_world_snapshot

    snapshot = read_world_snapshot(world_snapshot)

    # Create first app instance and post a message
    app1 = create_app(snapshot_path=world_snapshot)
    client1 = TestClient(app1)

    payload = {
        "patient_id": snapshot.patients[0].patient_id,
        "channel": "chat",
        "body": "Message from app1",
    }
    response1 = client1.post("/messages", json=payload)
    assert response1.status_code == 201
    message_id = response1.json()["message_id"]

    # Verify the message is visible in app1
    response = client1.get("/messages")
    assert response.status_code == 200
    messages1 = response.json()
    message_ids1 = [m["message_id"] for m in messages1]
    assert message_id in message_ids1

    # Create second app instance from the same snapshot
    app2 = create_app(snapshot_path=world_snapshot)
    client2 = TestClient(app2)

    # Verify the message is NOT visible in app2
    response = client2.get("/messages")
    assert response.status_code == 200
    messages2 = response.json()
    message_ids2 = [m["message_id"] for m in messages2]
    assert message_id not in message_ids2

    # Verify the message counts match the world messages count
    assert len(messages1) == len(snapshot.messages) + 1
    assert len(messages2) == len(snapshot.messages)
