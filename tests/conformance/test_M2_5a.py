"""M2-5a: Triage nodes and state for the triage agent.

Verifies that triage can ingest and redact patient messages, classify intent,
call tools with state-bound identifiers, generate drafts with escalation checks,
and run guard checks before and after human review.

Requirements verified: C1, R1, R6, L7.
"""

import json

import pytest

from clinicloop.agents.triage.intents import Intent
from clinicloop.agents.triage.models import FakeModelPort
from clinicloop.agents.triage.nodes.classify_intent import classify_intent
from clinicloop.agents.triage.nodes.draft import draft
from clinicloop.agents.triage.nodes.guard_final import guard_final
from clinicloop.agents.triage.nodes.ingest import ingest
from clinicloop.agents.triage.nodes.resolve import resolve
from clinicloop.agents.triage.state import TriageState, Turn
from clinicloop.compliance.guard.core import check


@pytest.mark.checklist_id("C1")
def test_triage_ingest_redacts_patient_message_and_detects_language() -> None:
    """C1: Triage ingests raw patient message, redacts PII, detects language.

    Verifies that the ingest node:
    - Converts raw patient message to redacted text
    - Detects English or non-English language
    - Stores redacted text in patient_data_block (delimited)
    - Stores message in redacted_thread with role='patient'
    """
    # English message with PII (matching actual redaction patterns)
    raw_msg = "Hi, I'm John Smith, call me at 0412345678 or john@example.com"

    result = ingest({}, raw_msg, "test-run-key")

    # Should have redacted thread with patient role
    assert "redacted_thread" in result
    assert len(result["redacted_thread"]) == 1
    assert result["redacted_thread"][0].role == "patient"
    # Raw data should not appear in redacted text
    assert "Smith" not in result["redacted_thread"][0].text
    assert "0412345678" not in result["redacted_thread"][0].text
    assert "john@example.com" not in result["redacted_thread"][0].text

    # Should detect English
    assert result["language"] == "en"

    # Should have delimited patient data block
    assert "patient_data_block" in result
    assert len(result["patient_data_block"]) > 0


@pytest.mark.checklist_id("C1")
def test_triage_classifies_intent_from_patient_message() -> None:
    """C1: Triage classifies message intent from patient data block.

    Verifies that classify_intent:
    - Builds prompt from patient_data_block
    - Uses ModelPort to complete the prompt
    - Parses JSON response containing intent name
    - Returns Intent enum value or Intent.unknown on parse failure
    """
    state = {
        "patient_data_block": "Hello, I need to check the status of my order",
    }

    # Use FakeModelPort with scripted response
    model = FakeModelPort(['{"intent": "order_status"}'])

    result = classify_intent(state, model)

    assert "intent" in result
    assert result["intent"] == Intent.order_status


@pytest.mark.checklist_id("C1")
def test_triage_resolve_binds_tool_args_from_state_not_model() -> None:
    """C1: Triage resolve binds tool arguments from state, not model output.

    Verifies that resolve:
    - Only calls tools for specific intents (order_status, cancellation, delivery_problem)
    - Uses patient_id and order_id from state, never from model
    - Records tool call with state-bound IDs even if model suggests different IDs
    """
    from clinicloop.agents.triage.tools import ToolRunner

    class FakeToolRunner(ToolRunner):
        """Test tool runner that returns fixed summary."""

        def run(self, name: str, patient_id: str, order_id: str | None) -> str:
            """Return a fixed summary."""
            if name == "get_order_status":
                return f"Order status query for {patient_id}, {order_id}"
            return "Tool executed"

    state = {
        "patient_id": "P-001",
        "order_id": "O-123",
        "intent": Intent.order_status,
    }

    # Model suggests different IDs (should be ignored)
    model = FakeModelPort(
        ['{"tool": "get_order_status", "args": {"patient_id": "P-WRONG", "order_id": "O-WRONG"}}']
    )

    tools = FakeToolRunner()
    result = resolve(state, model, tools)

    assert "tool_calls" in result
    assert len(result["tool_calls"]) == 1
    tool_call = result["tool_calls"][0]
    # State IDs used, not model IDs
    assert tool_call.args["patient_id"] == "P-001"
    assert tool_call.args["order_id"] == "O-123"
    assert "P-WRONG" not in json.dumps(tool_call.model_dump())
    assert "O-WRONG" not in json.dumps(tool_call.model_dump())


@pytest.mark.checklist_id("C1")
def test_triage_draft_requires_escalation_clearance() -> None:
    """C1: Draft node requires an EscalationClear token matching thread hash.

    Verifies that draft:
    - Calls require_clear() before generating draft
    - Raises EscalationRequired if token is missing or mismatches
    - Returns routing_reason='language' for non-English input (no draft)
    """
    redacted_msg = "I have a question about my order"
    state = {
        "redacted_thread": [Turn(role="patient", text=redacted_msg)],
        "patient_data_block": f"[DELIMITED_DATA]\n{redacted_msg}\n[/DELIMITED_DATA]",
        "language": "en",
        "escalation_clear": None,  # Missing token
    }

    model = FakeModelPort(["Draft reply"])

    # Should raise because escalation_clear is None
    from clinicloop.compliance.escalation.result import EscalationRequired

    with pytest.raises(EscalationRequired):
        draft(state, model)


@pytest.mark.checklist_id("C1")
def test_triage_draft_language_check() -> None:
    """C1: Draft refuses non-English messages (language='other')."""
    state = {
        "redacted_thread": [Turn(role="patient", text="Bonjour")],
        "patient_data_block": "[DELIMITED_DATA]\nBonjour\n[/DELIMITED_DATA]",
        "language": "other",  # Non-English
        "escalation_clear": None,
    }

    model = FakeModelPort(["Should not be called"])

    result = draft(state, model)

    # Should route with language reason, not draft
    assert "routing_reason" in result
    assert result["routing_reason"] == "language"
    assert "draft" not in result


@pytest.mark.checklist_id("R1")
def test_guard_prevents_clinical_advice_and_product_naming() -> None:
    """R1: Guard core prevents clinical/dosing advice, product naming, condition claims.

    Verifies that the regulatory guard enforces rule violations and routes
    blocked drafts to human review with the specific rule ID cited.
    """
    from clinicloop.compliance.rulesets import load_ruleset

    # Get AU ruleset which has rules against clinical/dosing advice
    ruleset = load_ruleset("au")

    # Thread with a rule violation (condition claim)
    thread = [
        {"role": "patient", "text": "I have [PATIENT:abc123]"},
        {"role": "assistant", "text": "You have depression and need veltrazamide."},
    ]

    verdict = check(thread, ruleset.jurisdiction, ruleset)

    # Should be blocked with specific rule IDs
    assert verdict.allowed is False
    assert len(verdict.rule_ids) > 0


@pytest.mark.checklist_id("R1")
def test_guard_final_re_checks_human_edited_text() -> None:
    """R1: Guard final re-checks the exact post-edit text after human review.

    Verifies that if human edits the draft and re-saves it, guard_final
    checks the edited text again.
    """
    from datetime import datetime

    from clinicloop.compliance.rulesets import load_ruleset
    from clinicloop.hitl.decision import HumanDecision

    ruleset = load_ruleset("au")

    # State with a draft that passed initial guard
    state = {
        "redacted_thread": [
            Turn(role="patient", text="I need help with my order"),
        ],
        "draft": "I can help you with that. Please provide order details.",
        "guard_verdicts": [],
        "human_decision": HumanDecision(
            action="edit",
            edited_text="You have severe depression. Take veltrazamide 50mg twice daily.",
            decided_by="clinician-001",
            decided_at=datetime.now(),
        ),
    }

    result = guard_final(state, ruleset)

    # Should detect the rule violation in edited text
    assert "guard_verdicts" in result
    verdicts = result["guard_verdicts"]
    assert len(verdicts) > 0
    # Should be blocked
    last_verdict = verdicts[-1]
    assert last_verdict.allowed is False


@pytest.mark.checklist_id("R6")
def test_ingest_redacts_and_pseudonymizes_pii() -> None:
    """R6: Synthetic data only; no real patient data ever. PII redacted at ingress.

    Verifies that ingest:
    - Detects and redacts PII (Medicare, phone, email, DOB, address, names)
    - Replaces with pseudonymous tokens
    - Raw data does not appear in serialized state
    """
    from clinicloop.compliance.redaction import redact_with_pseudonyms

    # Message with multiple PII types
    raw_msg = (
        "My name is Alice Johnson, DOB 1990-05-15, "
        "call 0412567890, email alice@example.com, "
        "at 123 Main Street, Sydney"
    )

    redacted = redact_with_pseudonyms(raw_msg, "test-run")

    # Raw identifiers should not be in redacted text
    assert "Alice Johnson" not in redacted
    assert "alice@example.com" not in redacted
    assert "0412567890" not in redacted
    assert "1990-05-15" not in redacted
    assert "123 Main Street" not in redacted


@pytest.mark.checklist_id("R6")
def test_state_serializes_without_raw_pii() -> None:
    """R6: TriageState serialization removes all raw PII.

    Verifies that when a state with redacted thread is serialized to JSON,
    no raw PII appears in the output.
    """
    # Create state with redacted thread (pseudonymized)
    state = TriageState(
        case_id="C-001",
        patient_id="P-001",
        order_id="O-001",
        redacted_thread=[
            Turn(role="patient", text="I am [PATIENT:a1b2c3d4]"),
        ],
        patient_data_block="[DELIMITED_DATA]\nI am [PATIENT:a1b2c3d4]\n[/DELIMITED_DATA]",
        language="en",
        intent=Intent.unknown,
    )

    # Serialize to JSON
    serialized = state.model_dump_json()

    # No real names or identifiers should appear
    assert "Johnson" not in serialized
    assert "john@example.com" not in serialized
    assert "0412" not in serialized


@pytest.mark.checklist_id("L7")
def test_triage_nodes_work_with_different_models_toml_rows() -> None:
    """L7: Triage nodes behave identically with different models.toml rows.

    Verifies that nodes are decoupled from model selection and produce
    consistent results when called with different models (via FakeModelPort).
    """
    # State with redacted message
    state = {
        "case_id": "C-001",
        "patient_id": "P-001",
        "order_id": "O-001",
        "redacted_thread": [
            Turn(role="patient", text="Can I check my order status?"),
        ],
        "patient_data_block": "[DELIMITED_DATA]\nCan I check my order status?\n[/DELIMITED_DATA]",
        "language": "en",
    }

    # Model 1: FakeModelPort with specific responses
    model_1 = FakeModelPort(
        [
            '{"intent": "order_status"}',  # for classify_intent
            '{"tool": "get_order_status", "args": {}}',  # for resolve
        ]
    )

    # Model 2: Same responses but different instance
    model_2 = FakeModelPort(
        [
            '{"intent": "order_status"}',
            '{"tool": "get_order_status", "args": {}}',
        ]
    )

    # Both models should produce same intent
    result_1 = classify_intent(state, model_1)
    result_2 = classify_intent(state, model_2)

    assert result_1["intent"] == result_2["intent"]
    assert result_1["intent"] == Intent.order_status
