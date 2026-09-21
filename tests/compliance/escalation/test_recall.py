"""Test escalation detection recall on fixture cases."""

import json
from pathlib import Path

import pytest

from clinicloop.compliance.escalation.detector import detect
from clinicloop.compliance.rulesets import load_ruleset


@pytest.fixture
def ruleset():
    """Load AU ruleset."""
    return load_ruleset("au")


@pytest.fixture
def test_cases():
    """Load test cases from JSONL fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "cases.jsonl"
    cases = []
    with open(fixture_path) as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    return cases


def test_detector_fixture_recall_is_one(ruleset, test_cases):
    """AC1: Recall is 1.0 on the five escalation categories.

    Every case labelled adverse_event, suspected_misuse, distress, pregnancy,
    or clinical_advice must return that category. Every 'none' case must
    return 'none'.
    """
    categories = {
        "adverse_event",
        "suspected_misuse",
        "distress",
        "pregnancy",
        "clinical_advice",
    }

    misses = []

    for case in test_cases:
        label = case["label"]
        thread = case["thread"]

        result = detect(thread, ruleset)

        if label in categories:
            if result.category != label:
                misses.append(
                    {
                        "label": label,
                        "got": result.category,
                        "thread": thread,
                    }
                )
        elif label == "none":
            if result.category != "none":
                misses.append(
                    {
                        "label": label,
                        "got": result.category,
                        "thread": thread,
                    }
                )

    # Print misses for debugging
    for miss in misses:
        print(f"MISS: expected {miss['label']}, got {miss['got']}, thread={miss['thread']}")

    assert misses == []
