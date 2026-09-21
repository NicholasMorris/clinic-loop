"""Test failure modes: classifier errors and timeouts."""

from __future__ import annotations

import time

import pytest

from clinicloop.compliance.escalation.detector import detect
from clinicloop.compliance.rulesets import Ruleset, load_ruleset


@pytest.fixture
def ruleset() -> Ruleset:
    """Load AU ruleset."""
    return load_ruleset("au")


def test_classifier_error_and_timeout_escalate_as_detector_error(
    ruleset: Ruleset,
) -> None:
    """AC7: Classifier exceptions and timeouts return detector_error category.

    No EscalationClear token is produced for detector_error.
    """
    thread = [{"role": "patient", "text": "What time is my appointment?"}]

    # Test 1: Classifier that raises an exception
    def classifier_raises(_thread):  # type: ignore[no-untyped-def]
        """Raises an error."""
        raise ValueError("database connection failed")

    result = detect(thread, ruleset, classifier=classifier_raises)
    assert result.category == "detector_error"
    assert result.clear is None, "detector_error should not produce a clear token"
    assert any(
        "database connection failed" in s.detail for s in result.evidence if s.source == "error"
    )

    # Test 2: Classifier that sleeps past timeout
    def classifier_sleeps(_thread):  # type: ignore[no-untyped-def]
        """Sleeps past the timeout."""
        time.sleep(0.1)
        return None

    result = detect(thread, ruleset, classifier=classifier_sleeps, timeout_seconds=0.05)
    assert result.category == "detector_error"
    assert result.clear is None
    assert any("timeout" in s.detail.lower() for s in result.evidence if s.source == "error")

    # Test 3: Slow classifier (should complete within 1 second)
    start = time.time()
    result = detect(thread, ruleset, classifier=classifier_sleeps, timeout_seconds=0.05)
    elapsed = time.time() - start
    assert elapsed < 1.0, f"detect() should return quickly even on timeout, took {elapsed}s"

    # Test 4: Classifier that raises a different exception type
    def classifier_type_error(_thread):  # type: ignore[no-untyped-def]
        """Raises TypeError."""
        raise TypeError("invalid type")

    result = detect(thread, ruleset, classifier=classifier_type_error)
    assert result.category == "detector_error"
    assert any("TypeError" in s.detail for s in result.evidence if s.source == "error")
