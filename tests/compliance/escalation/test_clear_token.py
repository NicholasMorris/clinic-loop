"""Test escalation clear token mechanics."""

import json

import pytest

from clinicloop.compliance.escalation.detector import detect
from clinicloop.compliance.escalation.gate import draft
from clinicloop.compliance.escalation.result import EscalationClear, EscalationClearForbidden, EscalationRequired
from clinicloop.compliance.rulesets import load_ruleset


@pytest.fixture
def ruleset():
    """Load AU ruleset."""
    return load_ruleset("au")


def test_clear_token_is_detector_only_and_required_by_draft(ruleset):
    """AC3: Direct construction of EscalationClear raises.

    The draft entry point requires a matching token or raises EscalationRequired.
    """
    # Direct construction should raise
    with pytest.raises(EscalationClearForbidden):
        EscalationClear(text_sha256="abc123")

    # detect() with a non-escalating thread returns a clear token
    thread = [{"role": "patient", "text": "What time is my appointment?"}]
    result = detect(thread, ruleset)
    assert result.category == "none"
    assert result.clear is not None

    # draft() without a token raises
    def dummy_drafter(t):  # type: ignore[no-untyped-def]
        return "response"

    with pytest.raises(EscalationRequired):
        draft(thread, None, dummy_drafter)

    # draft() with a valid clear token succeeds
    response = draft(thread, result.clear, dummy_drafter)
    assert response == "response"

    # detect() with an escalating thread returns no clear token
    escalated_thread = [{"role": "patient", "text": "I want to kill myself."}]
    escalated_result = detect(escalated_thread, ruleset)
    assert escalated_result.category == "distress"
    assert escalated_result.clear is None

    # draft() called after escalation raises (no token)
    with pytest.raises(EscalationRequired):
        draft(escalated_thread, None, dummy_drafter)


def test_token_bound_to_thread_hash(ruleset):
    """AC4: Token's text_sha256 must match the thread being drafted.

    A token from thread A cannot be used for thread B.
    """
    thread_a = [{"role": "patient", "text": "What is my delivery date?"}]
    thread_b = [{"role": "patient", "text": "Can I reschedule?"}]

    # Get clear token for thread A
    result_a = detect(thread_a, ruleset)
    clear_a = result_a.clear
    assert clear_a is not None

    # Try to draft thread B with token A
    def dummy_drafter(t):  # type: ignore[no-untyped-def]
        return "response"

    # Should fail because token_sha256 doesn't match
    with pytest.raises(EscalationRequired):
        draft(thread_b, clear_a, dummy_drafter)

    # Should succeed if we use matching token
    result_b = detect(thread_b, ruleset)
    clear_b = result_b.clear
    response = draft(thread_b, clear_b, dummy_drafter)
    assert response == "response"
