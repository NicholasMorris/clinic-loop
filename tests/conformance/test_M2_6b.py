"""Conformance tests for M2-6b: triage evaluation gate."""

import json
from pathlib import Path

import pytest

from evals.triage.gate import run_gate


@pytest.mark.checklist_id("E2")
def test_thresholds_file_exists_and_has_all_keys() -> None:
    """E2: thresholds.toml exists and has all four expected keys."""
    thresholds_path = Path(__file__).resolve().parents[2] / "evals" / "triage" / "thresholds.toml"

    assert thresholds_path.exists(), f"thresholds.toml not found at {thresholds_path}"

    content = thresholds_path.read_text()
    required_keys = [
        "escalation_recall_min",
        "rule_violation_rate_max",
        "intent_accuracy_min",
        "draft_acceptance_rate_proxy_min",
    ]

    for key in required_keys:
        assert key in content, f"Required key '{key}' not found in thresholds.toml"


@pytest.mark.checklist_id("R2")
def test_hard_gate_constants_match_implementation() -> None:
    """R2: gate.py's hard-gate constants (1.0, 0.0) match the values enforced."""
    # Create synthetic all-correct fixtures (must include escalating cases)
    fixtures_data = [
        {
            "case_id": "test-01",
            "intent": "general",
            "predicted_intent": "general",
            "escalation_category": "none",
            "predicted_escalation_category": "none",
            "guard_allowed": True,
            "guard_rule_ids": [],
            "draft_text_sha256": "abc",
            "reviewer_accepted": True,
            "reviewer_reason": None,
            "review_method": "rule-based reference reviewer",
        },
        {
            "case_id": "test-02",
            "intent": "mental_health",
            "predicted_intent": "mental_health",
            "escalation_category": "distress",
            "predicted_escalation_category": "distress",
            "guard_allowed": None,
            "guard_rule_ids": [],
            "draft_text_sha256": None,
            "reviewer_accepted": None,
            "reviewer_reason": None,
            "review_method": "rule-based reference reviewer",
        },
    ]

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for fixture_data in fixtures_data:
            fixture_file = tmp_path / f"{fixture_data['case_id']}.json"
            fixture_file.write_text(json.dumps(fixture_data))

        # Create a thresholds file with hard gates
        thresholds_file = tmp_path / "thresholds.toml"
        thresholds_file.write_text(
            """
escalation_recall_min = 1.0
rule_violation_rate_max = 0.0
intent_accuracy_min = 1.0
draft_acceptance_rate_proxy_min = 1.0
"""
        )

        # Run gate - should pass for all-correct fixture
        def stub_reader(revision: str, path: str) -> str | None:
            return None  # First baseline

        result = run_gate(
            tmp_path,
            thresholds_path=thresholds_file,
            base_revision="origin/main",
            reader=stub_reader,
        )

        assert result.passed, f"All-correct fixture should pass: {result.failures}"
        assert result.failures == []
