"""TriageState: typed, validated state for the triage agent."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

from clinicloop.agents.triage.intents import Intent
from clinicloop.compliance.escalation.result import EscalationClear
from clinicloop.hitl.decision import HumanDecision


class Turn(BaseModel):
    """A single message in the redacted thread.

    Attributes:
        role: 'patient' or 'assistant'.
        text: The message text (redacted for patient messages).
    """

    model_config = ConfigDict(frozen=True)

    role: Literal["patient", "assistant"]
    text: str


class ToolCall(BaseModel):
    """A recorded tool call with its result.

    Attributes:
        name: Tool name.
        args: Tool arguments (bound from state, not from model output).
        result_summary: Short factual summary of the tool result.
    """

    name: str
    args: dict[str, str]
    result_summary: str


class TriageState(BaseModel):
    """State for the triage agent.

    Carries case identity, the redacted thread with patient text in a delimited field,
    detected intent, escalation result, tool calls, draft reply, guard verdicts,
    human decision and routing reason.

    Attributes:
        case_id: Unique case identifier.
        patient_id: Unique patient identifier.
        order_id: Order identifier (optional).
        redacted_thread: List of turns with PII redacted.
        patient_data_block: Delimited patient text for model instructions.
        language: Detected language ('en' or 'other'), or None if not yet detected.
        intent: Classified intent, or None if not yet classified.
        escalation_category: Escalation result category.
        escalation_clear: Token proving escalation check passed (for draft gate).
        tool_calls: List of tool calls made during resolve.
        draft: Generated reply text, or None if not drafted.
        guard_verdicts: Guard check verdicts (regulatory, final).
        human_decision: Human approval decision, or None if not yet decided.
        routing_reason: Why the message was routed (language, rule_block, etc).
        routing_rule_ids: Rule IDs that caused routing.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    case_id: str
    patient_id: str
    order_id: Optional[str] = None
    redacted_thread: list[Turn] = []
    patient_data_block: str = ""
    language: Optional[Literal["en", "other"]] = None
    intent: Optional[Intent] = None
    escalation_category: Optional[str] = None
    escalation_clear: Optional[EscalationClear] = None
    tool_calls: list[ToolCall] = []
    draft: Optional[str] = None
    guard_verdicts: list[dict] = []
    human_decision: Optional[HumanDecision] = None
    routing_reason: Optional[str] = None
    routing_rule_ids: tuple[str, ...] = ()

    @staticmethod
    def apply_update(state: "TriageState", update: dict) -> "TriageState":
        """Apply an update dict to a state, returning a new validated state.

        Args:
            state: The current state.
            update: Dictionary of fields to update.

        Returns:
            A new TriageState with the update applied.

        Raises:
            pydantic.ValidationError: If the update produces invalid state.
        """
        return TriageState.model_validate({**state.model_dump(), **update})
