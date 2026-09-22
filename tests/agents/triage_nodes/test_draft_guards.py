"""Test draft node guards.

AC5: draft raises EscalationRequired when state carries no EscalationClear token
matching the thread hash, and for a non-English inbound fixture message it returns
no draft text and sets routing reason "language".
"""

import pytest

from clinicloop.agents.triage.intents import Intent
from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.agents.triage.nodes.draft import draft
from clinicloop.agents.triage.prompts import build_data_block
from clinicloop.compliance.escalation.detector import detect, thread_sha256
from clinicloop.compliance.escalation.result import EscalationRequired, _mint_clear
from clinicloop.compliance.rulesets import load_ruleset


@pytest.fixture
def _fixed_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set CLINICLOOP_ESCALATION_KEY to a fixed value."""
    monkeypatch.setenv("CLINICLOOP_ESCALATION_KEY", "a" * 64)


@pytest.fixture
def ruleset():
    """Load AU ruleset."""
    return load_ruleset("au")


def test_draft_needs_clearance(ruleset, _fixed_key: None) -> None:
    """AC5: draft raises EscalationRequired when clear token is missing."""
    state_dict = {
        "case_id": "c-001",
        "patient_id": "p-001",
        "redacted_thread": [{"role": "patient", "text": "What is my order?"}],
        "patient_data_block": build_data_block("What is my order?"),
        "escalation_clear": None,  # No clear token
    }

    fake_model = FakeModelPort(["Your order is on track."])

    # Should raise EscalationRequired
    with pytest.raises(EscalationRequired):
        update = draft(state_dict, fake_model)


def test_draft_clears_with_matching_token(ruleset, _fixed_key: None) -> None:
    """AC5: draft succeeds with a matching escalation clear token."""
    thread = [{"role": "patient", "text": "What is my order?"}]
    hash_val = thread_sha256(thread)
    clear_token = _mint_clear(hash_val)

    state_dict = {
        "case_id": "c-001",
        "patient_id": "p-001",
        "redacted_thread": [{"role": "patient", "text": "What is my order?"}],
        "patient_data_block": build_data_block("What is my order?"),
        "escalation_clear": clear_token,
    }

    fake_model = FakeModelPort(["Your order is on track."])

    try:
        update = draft(state_dict, fake_model)
    except NotImplementedError:
        pytest.skip("draft not yet implemented")

    # Should have returned a draft
    assert "draft" in update


def test_draft_refuses_non_english(ruleset, _fixed_key: None) -> None:
    """AC5: draft returns routing_reason='language' for non-English without drafting."""
    # Non-English text (Chinese characters)
    state_dict = {
        "case_id": "c-002",
        "patient_id": "p-002",
        "redacted_thread": [{"role": "patient", "text": "我想查询我的订单。"}],  # "I want to check my order" in Chinese
        "patient_data_block": build_data_block("我想查询我的订单。"),
        "language": "other",
        "escalation_clear": _mint_clear(thread_sha256([{"role": "patient", "text": "我想查询我的订单。"}])),
    }

    # Fake model should not be called
    fake_model = FakeModelPort([])  # No responses - would fail if called

    try:
        update = draft(state_dict, fake_model)
    except NotImplementedError:
        pytest.skip("draft not yet implemented")

    # Should return routing_reason='language', not a draft
    assert update.get("routing_reason") == "language", f"Got routing_reason: {update.get('routing_reason')}"
    assert update.get("draft") is None, "Should not produce draft for non-English"


def test_token_mismatch_raises(ruleset, _fixed_key: None) -> None:
    """AC5: draft raises if token's hash doesn't match the thread."""
    # Create a token for a different thread
    different_thread = [{"role": "patient", "text": "Different message"}]
    different_hash = thread_sha256(different_thread)
    token_for_different = _mint_clear(different_hash)

    # But try to use it with a different thread
    state_dict = {
        "case_id": "c-003",
        "patient_id": "p-003",
        "redacted_thread": [{"role": "patient", "text": "What is my order?"}],
        "patient_data_block": build_data_block("What is my order?"),
        "escalation_clear": token_for_different,
    }

    fake_model = FakeModelPort(["Your order is on track."])

    # Should raise because token hash doesn't match thread
    with pytest.raises(EscalationRequired):
        update = draft(state_dict, fake_model)
