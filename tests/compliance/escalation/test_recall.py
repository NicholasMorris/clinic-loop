"""Test escalation detection recall on fixture cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from clinicloop.compliance.escalation.detector import detect
from clinicloop.compliance.rulesets import Ruleset, load_ruleset


@pytest.fixture
def ruleset() -> Ruleset:
    """Load AU ruleset."""
    return load_ruleset("au")


@pytest.fixture
def test_cases() -> list[dict[str, Any]]:
    """Load test cases from JSONL fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "cases.jsonl"
    cases: list[dict[str, Any]] = []
    with open(fixture_path) as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    return cases


def test_detector_fixture_recall_is_one(ruleset: Ruleset, test_cases: list[dict[str, Any]]) -> None:
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
