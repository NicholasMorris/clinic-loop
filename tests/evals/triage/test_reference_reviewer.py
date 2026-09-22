"""Test the reference reviewer against fixtures."""

import json
from pathlib import Path

import pytest

from clinicloop.compliance.guard.verdict import GuardVerdict
from clinicloop.compliance.rulesets import load_ruleset
from evals.triage.golden.loader import ConfigurationError, load_intent_elements
from evals.triage.reference_reviewer import review


@pytest.fixture
def reviewer_cases():
    """Load reviewer fixture cases from JSONL."""
    fixture_path = Path(__file__).parent / "fixtures" / "reviewer_cases.jsonl"
    cases = []
    with open(fixture_path) as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    return cases


@pytest.fixture
def ruleset():
    """Load AU ruleset."""
    return load_ruleset("au")


def test_reviewer_verdicts_match_labels_and_name_the_failing_rule(reviewer_cases, ruleset):
    """AC3: Reviewer returns correct verdict and names the failing rule."""
    elements = load_intent_elements()

    for case in reviewer_cases:
        # Build a GuardVerdict object
        verdict = GuardVerdict(
            allowed=case["guard_allowed"],
            rule_ids=tuple(case["guard_rule_ids"]),
            jurisdiction="au",
            ruleset_version=ruleset.version,
            text_sha256="dummy_hash",
        )

        # Call review
        result = review(
            draft=case["draft"],
            guard_verdict=verdict,
            intent=case["intent"],
            elements=elements,
            ruleset=ruleset,
        )

        # Check accepted status
        assert result.accepted == case["expected_accepted"], (
            f"Case {case['case_id']}: expected accepted={case['expected_accepted']}, "
            f"got {result.accepted}"
        )

        # Check reason
        assert result.reason == case["expected_reason"], (
            f"Case {case['case_id']}: expected reason={case['expected_reason']}, "
            f"got {result.reason}"
        )


def test_reviewer_with_missing_elements_raises_configuration_error(
    reviewer_cases, ruleset, tmp_path
):
    """AC3: Reviewer raises ConfigurationError when elements cannot be loaded."""
    from unittest.mock import patch

    missing_case = reviewer_cases[0]

    # Mock load_intent_elements to raise ConfigurationError
    with pytest.raises(ConfigurationError):
        with patch(
            "evals.triage.reference_reviewer.load_intent_elements",
            side_effect=ConfigurationError("intent_elements.toml not found"),
        ):
            review(
                draft=missing_case["draft"],
                guard_verdict=GuardVerdict(
                    allowed=True,
                    rule_ids=(),
                    jurisdiction="au",
                    ruleset_version=ruleset.version,
                    text_sha256="dummy_hash",
                ),
                intent=missing_case["intent"],
                elements=None,  # Force reload which will hit the mocked function
                ruleset=ruleset,
            )
