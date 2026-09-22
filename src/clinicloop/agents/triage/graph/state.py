"""GraphState: TypedDict for LangGraph state matching TriageState fields."""

from typing import Any, Literal, Optional, TypedDict

from clinicloop.agents.triage.intents import Intent
from clinicloop.compliance.escalation.result import EscalationClear
from clinicloop.compliance.guard.verdict import GuardVerdict
from clinicloop.hitl.decision import HumanDecision


class Turn(TypedDict, total=False):
    """A single message in the redacted thread (for dict representation)."""

    role: Literal["patient", "assistant"]
    text: str


class ToolCall(TypedDict, total=False):
    """A recorded tool call with its result (for dict representation)."""

    name: str
    args: dict[str, str]
    result_summary: str


class GraphState(TypedDict, total=False):
    """State for the triage graph (LangGraph StateGraph).

    This TypedDict has exactly the same field names as TriageState for
    compatibility with the M2-5a node functions. Fields are total=False
    so they start absent and are added by nodes.

    Attributes:
        case_id: Unique case identifier (required).
        patient_id: Unique patient identifier (required).
        order_id: Order identifier (optional).
        redacted_thread: List of turns with PII redacted.
        patient_data_block: Delimited patient text for model instructions.
        language: Detected language ('en' or 'other'), or None.
        intent: Classified intent, or None.
        escalation_category: Escalation result category.
        escalation_clear: Token proving escalation check passed.
        tool_calls: List of tool calls made during resolve.
        draft: Generated reply text, or None.
        guard_verdicts: Guard check verdicts (regulatory, final).
        human_decision: Human approval decision, or None.
        routing_reason: Why the message was routed.
        routing_rule_ids: Rule IDs that caused routing.
        next: Tuple of next node names (LangGraph internal).
    """

    case_id: str
    patient_id: str
    order_id: Optional[str]
    redacted_thread: list[Any]
    patient_data_block: str
    language: Optional[Literal["en", "other"]]
    intent: Optional[Intent]
    escalation_category: Optional[str]
    escalation_clear: Optional[EscalationClear]
    tool_calls: list[Any]
    draft: Optional[str]
    guard_verdicts: list[GuardVerdict]
    human_decision: Optional[HumanDecision]
    routing_reason: Optional[str]
    routing_rule_ids: tuple[str, ...]
    next: tuple[str, ...]
