"""Test escalation clear token mechanics."""

from __future__ import annotations

import dataclasses

import pytest

from clinicloop.compliance.escalation.detector import detect
from clinicloop.compliance.escalation.gate import draft
from clinicloop.compliance.escalation.result import (
    EscalationClear,
    EscalationClearForbidden,
    EscalationRequired,
)
from clinicloop.compliance.rulesets import Ruleset, load_ruleset


@pytest.fixture
def ruleset() -> Ruleset:
    """Load AU ruleset."""
    return load_ruleset("au")


@pytest.fixture
def _fixed_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set CLINICLOOP_ESCALATION_KEY to a fixed value so no key file is written."""
    # Fixed 32-byte key as hex (64 characters)
    key_hex = "a" * 64
    monkeypatch.setenv("CLINICLOOP_ESCALATION_KEY", key_hex)


def test_clear_token_is_detector_only_and_required_by_draft(
    ruleset: Ruleset, _fixed_key: None
) -> None:
    """AC3: Direct construction of EscalationClear with wrong MAC raises.

    The draft entry point requires a matching token or raises EscalationRequired.
    """
    # Direct construction with wrong MAC should raise
    with pytest.raises(EscalationClearForbidden):
        EscalationClear(text_sha256="abc123", mac="wrongmac")

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


def test_token_bound_to_thread_hash(ruleset: Ruleset, _fixed_key: None) -> None:
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


def test_token_serialization_round_trip(ruleset: Ruleset, _fixed_key: None) -> None:
    """A token from detect() rebuilt from dataclasses.asdict is accepted.

    This proves tokens can be serialized and restored for checkpointing.
    """
    thread = [{"role": "patient", "text": "What is my delivery date?"}]
    result = detect(thread, ruleset)
    token = result.clear
    assert token is not None

    # Serialize and rebuild
    token_dict = dataclasses.asdict(token)
    rebuilt = EscalationClear(**token_dict)

    # Should be equal and work with draft
    assert rebuilt.text_sha256 == token.text_sha256
    assert rebuilt.mac == token.mac

    def dummy_drafter(t):  # type: ignore[no-untyped-def]
        return "response"

    response = draft(thread, rebuilt, dummy_drafter)
    assert response == "response"


def test_token_mac_validation_on_tampering(ruleset: Ruleset, _fixed_key: None) -> None:
    """A token whose text_sha256 was changed but keeps the old MAC is refused.

    This prevents accidental or intentional tampering with the hashed text.
    """
    thread = [{"role": "patient", "text": "What is my delivery date?"}]
    result = detect(thread, ruleset)
    token = result.clear
    assert token is not None

    # Create a tampered token with modified text_sha256 but same MAC
    # This should raise EscalationClearForbidden in __post_init__
    with pytest.raises(EscalationClearForbidden):
        tampered = EscalationClear(text_sha256="0" * 64, mac=token.mac)
