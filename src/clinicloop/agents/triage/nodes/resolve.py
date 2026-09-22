"""Resolve node: call tools for certain intents."""

import json
import re
from typing import Any

from clinicloop.agents.triage.intents import Intent
from clinicloop.agents.triage.state import ToolCall

# Intents that need tool resolution
TOOL_INTENTS = {Intent.order_status, Intent.cancellation, Intent.delivery_problem}

RESOLVE_PROMPT = """For the patient intent, which tool should be called?

Tools available:
- get_order_status: Look up an order's current status
- list_patient_orders: List all orders for the patient

Respond with JSON only:
{{"tool": "<tool_name>", "args": {{"patient_id": "<id>", "order_id": "<id>"}}}}
"""


def resolve(state: dict[str, Any], model, tools) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Call tools for order-related intents.

    Args:
        state: Current TriageState as dict.
        model: ModelPort with complete(prompt, *, sample_index=0) method.
        tools: ToolRunner protocol with run(name, patient_id, order_id) -> str.

    Returns:
        State update dict with tool_calls list (empty if intent doesn't need tools).
    """
    intent_val = state.get("intent")
    intent = Intent(intent_val) if isinstance(intent_val, str) else intent_val

    # Only process tool-needing intents
    if intent not in TOOL_INTENTS:
        return {}

    # Get model's tool choice
    prompt = RESOLVE_PROMPT
    response = model.complete(prompt, sample_index=0)

    # Parse JSON response
    tool_calls = []
    try:
        # Strip code fences
        response_text = response.strip()
        if response_text.startswith("```"):
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
            if match:
                response_text = match.group(1)
        else:
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if match:
                response_text = match.group(0)

        data = json.loads(response_text)
        tool_name = data.get("tool")
        # Model args are ignored; we use state IDs instead

        # Validate tool name
        if tool_name in ("get_order_status", "list_patient_orders"):
            # Get IDs from state (not from model)
            patient_id = state.get("patient_id", "")
            order_id = state.get("order_id")

            # Run the tool
            result_summary = tools.run(tool_name, patient_id, order_id)

            # Record the call with STATE IDs (not model args)
            tool_call = ToolCall(
                name=tool_name,
                args={"patient_id": patient_id, "order_id": order_id or ""},
                result_summary=result_summary,
            )
            tool_calls.append(tool_call)
    except (json.JSONDecodeError, AttributeError, KeyError):
        # Parse failure: no tool call made
        pass

    return {"tool_calls": tool_calls}
