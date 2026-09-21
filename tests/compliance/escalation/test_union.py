"""Test union rule: rules OR classifier."""

import pytest

from clinicloop.compliance.escalation.detector import detect
from clinicloop.compliance.rulesets import load_ruleset


@pytest.fixture
def ruleset():
    """Load AU ruleset."""
    return load_ruleset("au")


def test_either_detector_firing_escalates(ruleset):
    """AC2: Union rule holds in both directions.

    If rules match but classifier clears, result is non-none.
    If rules miss but classifier flags, result is non-none.
    If rules fire and classifier also flags, result uses priority order.
    """
    # Case 1: Rules match adverse_event, classifier returns None
    thread_adverse = [
        {
            "role": "patient",
            "text": "I took too many tablets and now I have chest pain.",
        }
    ]

    def classifier_clears(_thread):  # type: ignore[no-untyped-def]
        """Classifier that returns None (clears)."""
        return None

    result = detect(thread_adverse, ruleset, classifier=classifier_clears)
    assert result.category == "adverse_event", "Rules match should escalate even if classifier clears"

    # Case 2: Rules miss, classifier flags distress
    thread_benign = [{"role": "patient", "text": "What time is my appointment?"}]

    def classifier_flags_distress(_thread):  # type: ignore[no-untyped-def]
        """Classifier that returns distress."""
        return "distress"

    result = detect(thread_benign, ruleset, classifier=classifier_flags_distress)
    assert result.category == "distress", "Classifier match should escalate even if rules miss"

    # Case 3: Both rules and classifier fire; use priority (distress > adverse_event)
    thread_both = [
        {
            "role": "patient",
            "text": "I want to die and I also have chest pain from my medicine.",
        }
    ]

    def classifier_returns_adverse(_thread):  # type: ignore[no-untyped-def]
        """Classifier that returns adverse_event."""
        return "adverse_event"

    result = detect(thread_both, ruleset, classifier=classifier_returns_adverse)
    # Distress should win (higher priority)
    assert result.category == "distress"

    # Case 4: Rules fire but classifier raises (should still escalate with rules category)
    def classifier_raises(_thread):  # type: ignore[no-untyped-def]
        """Classifier that raises an exception."""
        raise ValueError("classifier error")

    result = detect(thread_adverse, ruleset, classifier=classifier_raises)
    assert result.category == "adverse_event", "Rules should escalate even if classifier raises"
    assert any(
        s.source == "error" for s in result.evidence
    ), "Error evidence should be recorded"
