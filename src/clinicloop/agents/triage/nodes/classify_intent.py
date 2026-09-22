"""Classify intent node: determine intent from patient message."""

import json
import re

from clinicloop.agents.triage.intents import Intent
from clinicloop.agents.triage.prompts import build_classify_prompt


def classify_intent(state: dict, model) -> dict:  # type: ignore[no-untyped-def]
    """Classify inbound message intent.

    Args:
        state: Current TriageState as dict.
        model: ModelPort with complete(prompt, *, sample_index=0) method.

    Returns:
        State update dict with intent field.
    """
    # Build prompt from patient data block
    data_block = state.get("patient_data_block", "")
    prompt = build_classify_prompt(data_block)

    # Get model response
    response = model.complete(prompt, sample_index=0)

    # Parse JSON response
    intent = Intent.unknown
    try:
        # Strip markdown code fences if present
        response_text = response.strip()
        if response_text.startswith("```"):
            # Extract JSON from code fence
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
            if match:
                response_text = match.group(1)
        else:
            # Try to extract JSON from the response if there's leading prose
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if match:
                response_text = match.group(0)

        data = json.loads(response_text)
        intent_name = data.get("intent")

        # Validate against Intent enum
        if intent_name:
            try:
                intent = Intent(intent_name)
            except ValueError:
                # Invalid intent name -> unknown
                intent = Intent.unknown
    except (json.JSONDecodeError, AttributeError):
        # Parse failure -> unknown
        intent = Intent.unknown

    return {"intent": intent}
