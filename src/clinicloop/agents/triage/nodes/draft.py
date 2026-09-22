"""Draft node: generate reply with escalation check and language check."""

from clinicloop.compliance.escalation.gate import require_clear

DRAFT_PROMPT = """Based on the patient message and any tools results, draft a brief, polite reply.

Rules:
- English only
- No clinical or dosing advice
- Never name any medicine
- Never claim a medical condition
- Be brief and polite

Provide the draft text only, no JSON."""


def draft(state: dict, model) -> dict:  # type: ignore[no-untyped-def]
    """Generate a draft reply with escalation and language checks.

    Args:
        state: Current TriageState as dict.
        model: ModelPort with complete(prompt, *, sample_index=0) method.

    Returns:
        State update dict with draft field (or routing_reason='language').

    Raises:
        EscalationRequired: If escalation_clear is missing or mismatches thread.
    """
    # Check language first
    language = state.get("language")
    if language == "other":
        # Non-English message: route instead of drafting
        return {"routing_reason": "language"}

    # Convert thread to dict format for gate validation
    redacted_thread = state.get("redacted_thread", [])
    thread_dicts = [{"role": turn.role, "text": turn.text} for turn in redacted_thread]

    # Require escalation clearance
    escalation_clear = state.get("escalation_clear")
    require_clear(thread_dicts, escalation_clear)

    # Build prompt with thread and tool results
    thread_text = "\n".join(f"{turn.role}: {turn.text}" for turn in redacted_thread)
    tool_summaries = ""
    tool_calls = state.get("tool_calls", [])
    if tool_calls:
        tool_summaries = "\n\nTool results:\n" + "\n".join(
            f"- {tc.name}: {tc.result_summary}" for tc in tool_calls
        )

    prompt = f"{DRAFT_PROMPT}\n\nThread:\n{thread_text}{tool_summaries}"

    # Generate draft
    draft_text = model.complete(prompt, sample_index=0).strip()

    return {"draft": draft_text}
