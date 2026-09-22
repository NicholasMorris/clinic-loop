"""Test classify_intent node.

AC3: classify_intent returns the labelled intent for every thread in the node-level
intent fixture under cassette replay, with the miss list printed and empty.
"""

import json
from pathlib import Path

import pytest

from clinicloop.agents.triage.intents import Intent
from clinicloop.agents.triage.models import CassetteModelPort, FakeModelPort
from clinicloop.agents.triage.nodes.classify_intent import classify_intent
from clinicloop.agents.triage.prompts import build_data_block


@pytest.fixture
def fixture_threads() -> list[dict]:
    """Load intent fixture threads."""
    fixture_path = Path(__file__).parent / "fixtures" / "intent_threads.jsonl"
    threads = []
    with open(fixture_path) as f:
        for line in f:
            threads.append(json.loads(line))
    return threads


@pytest.fixture
def cassette_paths() -> list[Path]:
    """Get cassette file paths."""
    cassette_dir = Path(__file__).parent / "cassettes"
    return [cassette_dir / "recorded_intent.jsonl"]


@pytest.fixture
def _fixed_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set CLINICLOOP_ESCALATION_KEY to a fixed value."""
    monkeypatch.setenv("CLINICLOOP_ESCALATION_KEY", "a" * 64)


def test_intent_matches_label_for_every_fixture_thread(
    fixture_threads: list[dict],
    cassette_paths: list[Path],
    _fixed_key: None,
) -> None:
    """AC3: All 50 fixture threads classify to their labelled intent via cassette."""
    model = CassetteModelPort(
        model_id="unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF",
        seed=42,
        cassette_paths=cassette_paths,
    )

    misses = []

    for thread_fixture in fixture_threads:
        thread_id = thread_fixture["id"]
        expected_intent = thread_fixture["label"]
        raw_text = thread_fixture["text"]

        # Build state as ingest would
        state_dict = {
            "case_id": f"test-{thread_id}",
            "patient_id": f"patient-{thread_id}",
            "redacted_thread": [{"role": "patient", "text": raw_text}],
            "patient_data_block": build_data_block(raw_text),
        }

        # Run classify_intent
        try:
            update = classify_intent(state_dict, model)
        except NotImplementedError:
            pytest.skip("classify_intent not yet implemented")

        # Check the result
        actual_intent = update.get("intent")

        # Compare intent value (handle both Intent enum and string)
        if isinstance(actual_intent, Intent):
            actual_value = actual_intent.value
        else:
            actual_value = str(actual_intent)

        if actual_value != expected_intent:
            misses.append(
                {
                    "thread_id": thread_id,
                    "expected": expected_intent,
                    "actual": actual_value,
                    "text": raw_text[:50],
                }
            )

    # Print misses for debugging
    if misses:
        print(f"\nIntent classification misses ({len(misses)}):")
        for miss in misses:
            print(f"  {miss['thread_id']}: expected {miss['expected']}, got {miss['actual']}")

    # Assert all matched
    assert misses == [], f"{len(misses)} threads misclassified"


def test_cassette_miss_raises(cassette_paths: list[Path], _fixed_key: None) -> None:
    """AC3: CassetteMiss is raised for unrecorded prompts."""
    from clinicloop.agents.triage.cassettes import CassetteMiss

    model = CassetteModelPort(
        model_id="unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF",
        seed=42,
        cassette_paths=cassette_paths,
    )

    # Build a state with a prompt that's not in the cassette
    state_dict = {
        "case_id": "test-miss",
        "patient_id": "patient-miss",
        "redacted_thread": [
            {
                "role": "patient",
                "text": "This is an unrecorded prompt that will not match any cassette.",
            }
        ],
        "patient_data_block": build_data_block(
            "This is an unrecorded prompt that will not match any cassette."
        ),
    }

    # Should raise CassetteMiss when trying to classify
    with pytest.raises(CassetteMiss):
        update = classify_intent(state_dict, model)


def test_out_of_enum_response_becomes_unknown(_fixed_key: None) -> None:
    """AC3: Model response outside Intent enum becomes Intent.unknown."""
    # Use FakeModelPort with a response that's not a valid intent
    fake_model = FakeModelPort(
        [
            '{"intent": "invalid_intent_name"}',
        ]
    )

    state_dict = {
        "case_id": "test-invalid",
        "patient_id": "patient-invalid",
        "redacted_thread": [{"role": "patient", "text": "What is my order?"}],
        "patient_data_block": build_data_block("What is my order?"),
    }

    try:
        update = classify_intent(state_dict, fake_model)
    except NotImplementedError:
        pytest.skip("classify_intent not yet implemented")

    # Should return unknown intent
    assert update.get("intent") == Intent.unknown or str(update.get("intent")) == "unknown"
