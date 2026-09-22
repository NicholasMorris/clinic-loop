"""Test tool binding in resolve node.

AC4: Tool arguments are bound from state: with a cassette whose model output names
patient_id "P-9999" and order_id "O-9999", the executed tool call carries the
patient_id and order_id held in TriageState, and the recorded call arguments
contain neither model-supplied value.
"""

import json
from pathlib import Path

import pytest

from clinicloop.agents.triage.intents import Intent
from clinicloop.agents.triage.nodes.resolve import resolve
from clinicloop.agents.triage.state import TriageState


class RecordingToolRunner:
    """Tool runner that records calls for verification."""

    def __init__(self) -> None:
        """Initialize with empty call record."""
        self.calls: list[dict[str, str | None]] = []

    def run(self, name: str, patient_id: str, order_id: str | None) -> str:
        """Record the call and return a summary."""
        self.calls.append(
            {
                "name": name,
                "patient_id": patient_id,
                "order_id": order_id,
            }
        )
        return f"Order {order_id} status: in transit"


@pytest.fixture
def _fixed_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set CLINICLOOP_ESCALATION_KEY to a fixed value."""
    monkeypatch.setenv("CLINICLOOP_ESCALATION_KEY", "a" * 64)


def test_patient_and_order_ids_come_from_state_not_the_model(
    _fixed_key: None,
) -> None:
    """AC4: State IDs are used, not model-supplied IDs."""
    # Build a state with specific patient and order IDs
    state_dict = {
        "case_id": "c-001",
        "patient_id": "p-state-001",
        "order_id": "o-state-001",
        "intent": Intent.order_status.value,
        "redacted_thread": [{"role": "patient", "text": "Where is my order?"}],
        "patient_data_block": "<<<PATIENT_DATA\nWhere is my order?\nPATIENT_DATA>>>",
    }

    # Create a fake model that tries to supply different IDs
    fake_model = type(
        "obj",
        (object,),
        {
            "complete": lambda self, prompt, sample_index=0: (
                '{"tool": "get_order_status", "args": {"patient_id": "P-9999", "order_id": "O-9999"}}'  # noqa: E501
            )
        },
    )()

    # Create a recording tool runner
    tool_runner = RecordingToolRunner()

    # Run resolve
    update = resolve(state_dict, fake_model, tool_runner)

    # Check the recorded call
    assert len(tool_runner.calls) > 0, "Should have made at least one tool call"
    call = tool_runner.calls[0]

    # Verify the IDs came from state, not from model output
    assert call["patient_id"] == "p-state-001", f"Expected state ID, got {call['patient_id']}"
    assert call["order_id"] == "o-state-001", f"Expected state ID, got {call['order_id']}"

    # Verify the state never contained the model-supplied values
    state = TriageState.model_validate({**state_dict, **update})
    state_json = json.dumps(state.model_dump(mode="json"))

    assert "P-9999" not in state_json, "Model-supplied patient_id leaked into state"
    assert "O-9999" not in state_json, "Model-supplied order_id leaked into state"


def test_resolve_for_tool_intents_only(_fixed_key: None) -> None:
    """AC4: resolve() makes no tool call for non-tool intents."""
    # Test with general_question intent (no tools needed)
    state_dict = {
        "case_id": "c-002",
        "patient_id": "p-002",
        "intent": Intent.general_question.value,
        "redacted_thread": [{"role": "patient", "text": "What are your hours?"}],
        "patient_data_block": "<<<PATIENT_DATA\nWhat are your hours?\nPATIENT_DATA>>>",
    }

    # Fake model would fail if called
    fake_model = type(
        "obj",
        (object,),
        {
            "complete": lambda self, prompt, sample_index=0: raise_on_call(
                "Model should not be called for general_question"
            )
        },
    )()

    tool_runner = RecordingToolRunner()

    update = resolve(state_dict, fake_model, tool_runner)

    # Should return empty update (no tool calls)
    assert update == {} or update.get("tool_calls") == []
    assert len(tool_runner.calls) == 0, "Should not call tools for non-tool intents"


def raise_on_call(msg: str) -> None:
    """Helper to fail if called."""
    raise AssertionError(msg)


def test_resolve_via_cassette_still_binds_ids_from_state(_fixed_key: None) -> None:
    """AC4: a compromised recorded response cannot leak model-supplied IDs either.

    tests/agents/triage_nodes/cassettes/synthetic_tool_binding.jsonl is a HAND-WRITTEN
    synthetic adversarial cassette (not a real recording): its response names
    patient_id "P-9999" and order_id "O-9999", keyed by the real hash of resolve's
    RESOLVE_PROMPT so CassetteModelPort actually finds it via the real prompt path.
    """
    from clinicloop.agents.triage.models import CassetteModelPort

    cassette_path = Path(__file__).parent / "cassettes" / "synthetic_tool_binding.jsonl"
    model = CassetteModelPort("synthetic", 42, [cassette_path])

    state_dict = {
        "case_id": "c-002",
        "patient_id": "p-state-002",
        "order_id": "o-state-002",
        "intent": Intent.order_status.value,
        "redacted_thread": [{"role": "patient", "text": "Where is my order?"}],
        "patient_data_block": "<<<PATIENT_DATA\nWhere is my order?\nPATIENT_DATA>>>",
    }
    tool_runner = RecordingToolRunner()

    update = resolve(state_dict, model, tool_runner)

    assert len(tool_runner.calls) == 1
    call = tool_runner.calls[0]
    assert call["patient_id"] == "p-state-002"
    assert call["order_id"] == "o-state-002"

    state = TriageState.model_validate({**state_dict, **update})
    state_json = json.dumps(state.model_dump(mode="json"))
    assert "P-9999" not in state_json
    assert "O-9999" not in state_json
