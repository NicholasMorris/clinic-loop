"""Test AC1: blocked POST /messages returns 422 and is not stored."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from clinicloop.evals.guard.corpus_loader import load_cases
from clinicloop.evals.guard.guard_case import GuardCase
from clinicloop.world.generator.snapshot import read_world_snapshot


@pytest.fixture
def corpus_cases() -> list[GuardCase]:
    """Load guard corpus cases.

    Returns:
        List of GuardCase objects filtered for block cases.
    """
    cases = load_cases()
    # Filter for block cases, at least one from each of 6 families
    families_covered = set()
    block_cases: list[GuardCase] = []
    for case in cases:
        if case.expected_verdict == "block" and case.family not in families_covered:
            block_cases.append(case)
            families_covered.add(case.family)
            if len(block_cases) >= 6:
                break
    return block_cases


def test_blocked_message_returns_422_with_rule_id_and_is_not_stored(
    client: TestClient,
    world_snapshot: Path,
    corpus_cases: list[GuardCase],
) -> None:
    """Test that blocked messages return 422 and are not stored.

    AC1: POST /messages with text from an expected-block corpus case
    returns 422 with a JSON body whose rule_ids contains the case's
    expected rule id, whose jurisdiction and ruleset_version fields are
    non-empty strings, and whose match entries each carry start and end
    integers and no "text" key; a following GET /messages returns the
    same message count as before the POST.

    Args:
        client: TestClient fixture.
        world_snapshot: Path to snapshot.
        corpus_cases: Blocked corpus cases.
    """
    snapshot = read_world_snapshot(world_snapshot)

    # Test each block case
    for case in corpus_cases:
        # Get initial message count
        response = client.get("/messages")
        assert response.status_code == 200
        initial_count = len(response.json())

        # Construct body from case's assistant message texts
        body = " ".join(msg.text for msg in case.thread if msg.role == "assistant")

        # POST the blocked message
        payload = {
            "patient_id": snapshot.patients[0].patient_id,
            "channel": "chat",
            "body": body,
        }
        response = client.post("/messages", json=payload)

        # Should return 422
        assert response.status_code == 422, (
            f"Case {case.case_id}: expected 422, got {response.status_code}"
        )

        # Check response body structure
        response_body = response.json()
        assert "rule_ids" in response_body, f"Case {case.case_id}: missing rule_ids"
        assert "jurisdiction" in response_body, f"Case {case.case_id}: missing jurisdiction"
        assert "ruleset_version" in response_body, f"Case {case.case_id}: missing ruleset_version"

        # Verify rule_ids is non-empty and contains the expected rule
        rule_ids = response_body["rule_ids"]
        assert isinstance(rule_ids, list), f"Case {case.case_id}: rule_ids should be a list"
        assert len(rule_ids) > 0, f"Case {case.case_id}: rule_ids should not be empty"
        assert case.expected_rule_id in rule_ids, (
            f"Case {case.case_id}: expected rule {case.expected_rule_id} not in {rule_ids}"
        )

        # Verify jurisdiction and ruleset_version are non-empty
        jurisdiction = response_body["jurisdiction"]
        ruleset_version = response_body["ruleset_version"]
        assert isinstance(jurisdiction, str) and len(jurisdiction) > 0
        assert isinstance(ruleset_version, str) and len(ruleset_version) > 0

        # Verify matches have start and end but no text
        if "matches" in response_body:
            matches = response_body["matches"]
            assert isinstance(matches, list)
            for match in matches:
                assert "start" in match, f"Case {case.case_id}: match missing start"
                assert "end" in match, f"Case {case.case_id}: match missing end"
                assert isinstance(match["start"], int), f"Case {case.case_id}: start should be int"
                assert isinstance(match["end"], int), f"Case {case.case_id}: end should be int"
                assert match["start"] < match["end"], f"Case {case.case_id}: start must be < end"
                assert "text" not in match, f"Case {case.case_id}: match should not have 'text' key"

            # Ensure the body text and any lexicon terms are not in the response
            assert body not in str(response_body), (
                f"Case {case.case_id}: message text leaked into response"
            )

        # Verify message count unchanged
        response = client.get("/messages")
        assert response.status_code == 200
        final_count = len(response.json())
        assert final_count == initial_count, (
            f"Case {case.case_id}: message count changed (was {initial_count}, now {final_count})"
        )
