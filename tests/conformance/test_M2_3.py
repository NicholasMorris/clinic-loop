"""Conformance tests for M2-3 escalation detection.

Tests R2 (escalation) and R1 (clinical advice refusal).
"""

from __future__ import annotations

import pytest

from clinicloop.compliance.escalation.detector import detect
from clinicloop.compliance.escalation.gate import draft
from clinicloop.compliance.escalation.result import EscalationRequired
from clinicloop.compliance.rulesets import Ruleset, load_ruleset


@pytest.fixture
def ruleset() -> Ruleset:
    """Load AU ruleset."""
    return load_ruleset("au")


@pytest.mark.checklist_id("R2")
def test_r2_adverse_event_escalation_recall(ruleset: Ruleset) -> None:
    """R2: Adverse events escalate immediately, never drafted.

    Requirement: Adverse events, suspected misuse, mental-health distress,
    pregnancy queries escalate immediately, never drafted.
    """
    # Adverse event should escalate
    thread = [
        {
            "role": "patient",
            "text": "I had an allergic reaction after taking my medicine. My face swelled up.",
        }
    ]

    result = detect(thread, ruleset)

    # Should be escalated
    assert result.category == "adverse_event"
    assert result.queue == "clinical_urgent"
    assert result.clear is None  # No clear token when escalated

    # draft() should refuse without a clear token
    def dummy_drafter(t):  # type: ignore[no-untyped-def]
        return "draft"

    with pytest.raises(EscalationRequired):
        draft(thread, None, dummy_drafter)


@pytest.mark.checklist_id("R1")
def test_r1_clinical_advice_escalation(ruleset: Ruleset) -> None:
    """R1: Clinical advice requests escalate, never drafted.

    Requirement: No agent produces clinical or dosing advice.
    """
    # Clinical advice request should escalate
    thread = [
        {
            "role": "patient",
            "text": "Should I increase my dose or keep it the same?",
        }
    ]

    result = detect(thread, ruleset)

    # Should be escalated
    assert result.category == "clinical_advice"
    assert result.queue == "prescriber_review"
    assert result.clear is None

    # draft() should refuse
    def dummy_drafter(t):  # type: ignore[no-untyped-def]
        return "draft"

    with pytest.raises(EscalationRequired):
        draft(thread, None, dummy_drafter)
