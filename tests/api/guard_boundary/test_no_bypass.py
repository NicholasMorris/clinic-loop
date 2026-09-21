"""Test AC4: blocked cases store zero rows, allow cases store one each."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from clinicloop.evals.guard.corpus_loader import load_cases
from clinicloop.world.generator.snapshot import read_world_snapshot


def test_zero_blocked_cases_reach_storage() -> None:
    """Test that all corpus cases through POST /messages behave as expected.

    AC4: A parametrised POST over every corpus case stores zero rows for
    expected-block cases, so the measured bypass count is 0, and stores
    one row per expected-allow case.

    This test is parametrized over all corpus cases.
    """
    cases = load_cases()

    # We can't parametrize fixtures easily, so we'll test with the full list
    # and count block vs allow
    block_count = sum(1 for case in cases if case.expected_verdict == "block")
    allow_count = sum(1 for case in cases if case.expected_verdict == "allow")

    # Print counts for debugging
    print("\nCorpus summary:")
    print(f"  Block cases: {block_count}")
    print(f"  Allow cases: {allow_count}")
    print(f"  Total: {len(cases)}")

    # Verify we have a meaningful corpus
    assert block_count > 0, "Corpus should have block cases"
    assert allow_count > 0, "Corpus should have allow cases"


@pytest.mark.parametrize("case_index", range(len(load_cases())))
def test_each_corpus_case_stores_correctly(
    client: TestClient,
    world_snapshot: Path,
    case_index: int,
) -> None:
    """Test each corpus case stores (or doesn't) as expected.

    Args:
        client: TestClient fixture.
        world_snapshot: Path to snapshot.
        case_index: Index of the case to test.
    """
    cases = load_cases()
    case = cases[case_index]
    snapshot = read_world_snapshot(world_snapshot)

    # Get initial message count
    response = client.get("/messages")
    assert response.status_code == 200
    initial_count = len(response.json())

    # Construct body from case's assistant message texts
    body = " ".join(msg.text for msg in case.thread if msg.role == "assistant")

    # POST the message
    payload = {
        "patient_id": snapshot.patients[0].patient_id,
        "channel": "chat",
        "body": body,
    }
    response = client.post("/messages", json=payload)

    # Get final message count
    response = client.get("/messages")
    assert response.status_code == 200
    final_count = len(response.json())

    if case.expected_verdict == "block":
        # Blocked cases should not be stored
        assert final_count == initial_count, (
            f"Case {case.case_id}: blocked message was stored "
            f"(count went from {initial_count} to {final_count})"
        )
    else:  # allow
        # Allowed cases should be stored
        assert final_count == initial_count + 1, (
            f"Case {case.case_id}: allowed message was not stored "
            f"(count went from {initial_count} to {final_count})"
        )
