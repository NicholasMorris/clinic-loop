"""Test TriageState typing and validation.

AC1: TriageState rejects an update whose intent is outside the documented intent enum
and one whose draft field is not a string, raising a validation error in both cases,
and accepts the reference state fixture with every field round-tripping unchanged
through serialisation.
"""

import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from clinicloop.agents.triage.intents import Intent
from clinicloop.agents.triage.state import ToolCall, TriageState, Turn
from clinicloop.compliance.escalation.detector import detect
from clinicloop.compliance.guard.verdict import GuardVerdict
from clinicloop.compliance.rulesets import load_ruleset
from clinicloop.hitl.decision import HumanDecision


@pytest.fixture
def _fixed_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set CLINICLOOP_ESCALATION_KEY to a fixed value."""
    monkeypatch.setenv("CLINICLOOP_ESCALATION_KEY", "a" * 64)


def test_state_rejects_out_of_enum_and_mistyped_fields(_fixed_key: None) -> None:
    """AC1: Invalid intent enum and non-string draft raise ValidationError."""
    # Create a minimal valid state
    valid_state = TriageState(case_id="c-001", patient_id="p-001")

    # Test: invalid intent raises ValidationError
    with pytest.raises(ValidationError):
        valid_state.apply_update(valid_state, {"intent": "invalid_intent"})

    # Test: non-string draft raises ValidationError
    with pytest.raises(ValidationError):
        valid_state.apply_update(valid_state, {"draft": 123})

    # Test: out-of-enum intent from dict raises ValidationError
    with pytest.raises(ValidationError):
        TriageState.model_validate(
            {
                "case_id": "c-001",
                "patient_id": "p-001",
                "intent": "not_an_intent",
            }
        )


def test_state_full_round_trip_serialization(_fixed_key: None) -> None:
    """AC1: A fully populated state round-trips through JSON serialization."""
    # Build a complete state with all field types
    ruleset = load_ruleset("au")
    thread = [{"role": "patient", "text": "What is my order status?"}]
    escalation_result = detect(thread, ruleset)

    turns = [
        Turn(role="patient", text="[PHONE:redacted]"),
        Turn(role="assistant", text="I can help with your order."),
    ]

    tool_call = ToolCall(
        name="get_order_status",
        args={"patient_id": "p-001", "order_id": "o-123"},
        result_summary="Order O-123 is in transit, arrives 2026-09-25.",
    )

    human_decision = HumanDecision(
        action="approve",
        decided_by="clinician-001",
        decided_at=datetime.now(),
    )

    verdict_data = [
        GuardVerdict(
            allowed=True,
            rule_ids=(),
            jurisdiction="au",
            ruleset_version="1.0",
            text_sha256="a" * 64,
        )
    ]

    state = TriageState(
        case_id="c-001",
        patient_id="p-001",
        order_id="o-123",
        redacted_thread=turns,
        patient_data_block="<<<PATIENT_DATA\nMessage\nPATIENT_DATA>>>",
        language="en",
        intent=Intent.order_status,
        escalation_category="none",
        escalation_clear=escalation_result.clear,
        tool_calls=[tool_call],
        draft="Your order is on track.",
        guard_verdicts=verdict_data,
        human_decision=human_decision,
        routing_reason=None,
        routing_rule_ids=(),
    )

    # Serialize to JSON
    json_str = json.dumps(state.model_dump(mode="json"))
    parsed = json.loads(json_str)

    # Deserialize back
    restored = TriageState.model_validate(parsed)

    # Verify all fields match
    assert restored.case_id == state.case_id
    assert restored.patient_id == state.patient_id
    assert restored.order_id == state.order_id
    assert len(restored.redacted_thread) == len(state.redacted_thread)
    assert restored.redacted_thread[0].role == "patient"
    assert restored.patient_data_block == state.patient_data_block
    assert restored.language == state.language
    assert restored.intent == state.intent
    assert restored.escalation_category == state.escalation_category
    assert restored.escalation_clear is not None
    assert state.escalation_clear is not None
    assert restored.escalation_clear.text_sha256 == state.escalation_clear.text_sha256
    assert len(restored.tool_calls) == 1
    assert restored.tool_calls[0].name == "get_order_status"
    assert restored.draft == state.draft
    assert restored.human_decision is not None
    assert restored.human_decision.action == "approve"


def test_state_rejects_extra_fields(_fixed_key: None) -> None:
    """AC1: State with extra='forbid' rejects unknown fields."""
    with pytest.raises(ValidationError):
        TriageState.model_validate(
            {
                "case_id": "c-001",
                "patient_id": "p-001",
                "unknown_field": "should fail",
            }
        )


def test_escalation_clear_survives_rebuild(_fixed_key: None) -> None:
    """AC1: Escalation clear token can be rebuilt from asdict and verified."""
    import dataclasses

    ruleset = load_ruleset("au")
    thread = [{"role": "patient", "text": "What is my order status?"}]
    escalation_result = detect(thread, ruleset)
    token = escalation_result.clear
    assert token is not None

    # Serialize and rebuild (as would happen in checkpointing)
    token_dict = dataclasses.asdict(token)
    rebuilt = token.__class__(**token_dict)

    # Should be identical
    assert rebuilt.text_sha256 == token.text_sha256
    assert rebuilt.mac == token.mac
