"""Test AC2: allowed POST /messages returns 201 with text_sha256."""

import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from clinicloop.evals.guard.corpus_loader import load_cases
from clinicloop.evals.guard.guard_case import GuardCase
from clinicloop.world.generator.snapshot import read_world_snapshot


@pytest.fixture
def allow_cases() -> list[GuardCase]:
    """Load guard corpus cases.

    Returns:
        List of GuardCase objects filtered for allow cases.
    """
    cases = load_cases()
    # Filter for allow cases
    allow_cases_list = [case for case in cases if case.expected_verdict == "allow"]
    return allow_cases_list[:5]  # Use first 5 for speed


def test_allowed_message_returns_201_with_text_sha256(
    client: TestClient,
    world_snapshot: Path,
    allow_cases: list[GuardCase],
) -> None:
    """Test that allowed messages return 201 with text_sha256.

    AC2: POST /messages with an expected-allow corpus case returns 201
    and a body whose text_sha256 equals sha256 of the exact stored text
    read back from GET /messages.

    Args:
        client: TestClient fixture.
        world_snapshot: Path to snapshot.
        allow_cases: Allowed corpus cases.
    """
    snapshot = read_world_snapshot(world_snapshot)

    # Test each allow case
    for case in allow_cases:
        # Construct body from case's assistant message texts
        body = " ".join(msg.text for msg in case.thread if msg.role == "assistant")

        # POST the allowed message
        payload = {
            "patient_id": snapshot.patients[0].patient_id,
            "channel": "chat",
            "body": body,
        }
        response = client.post("/messages", json=payload)

        # Should return 201
        assert response.status_code == 201, (
            f"Case {case.case_id}: expected 201, got {response.status_code}. Body: {response.text}"
        )

        # Check response body structure
        response_body = response.json()
        assert "text_sha256" in response_body, f"Case {case.case_id}: missing text_sha256"
        assert "message_id" in response_body, f"Case {case.case_id}: missing message_id"

        # Get the message ID
        message_id = response_body["message_id"]

        # Read the message back from GET /messages/{message_id}
        get_response = client.get(f"/messages/{message_id}")
        assert get_response.status_code == 200, f"Case {case.case_id}: failed to read message back"

        stored_message = get_response.json()
        assert "body" in stored_message, f"Case {case.case_id}: missing body in stored message"

        # Compute expected SHA256 of the stored body
        stored_body = stored_message["body"]
        expected_sha = hashlib.sha256(stored_body.encode("utf-8")).hexdigest()

        # Verify text_sha256 matches
        returned_sha = response_body["text_sha256"]
        assert returned_sha == expected_sha, (
            f"Case {case.case_id}: text_sha256 mismatch. "
            f"Returned: {returned_sha}, Expected: {expected_sha}"
        )
