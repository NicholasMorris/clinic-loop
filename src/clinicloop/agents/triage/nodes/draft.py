"""Draft node: generate reply with escalation check and language check."""


def draft(state: dict, model) -> dict:  # type: ignore[no-untyped-def]
    """Generate a draft reply with escalation and language checks.

    Requires state.escalation_clear to match the thread hash. Returns routing_reason
    'language' for non-English messages instead of drafting.

    Args:
        state: Current TriageState as dict.
        model: ModelPort with complete(prompt, *, sample_index=0) method.

    Returns:
        State update dict with draft field (or routing_reason='language').

    Raises:
        NotImplementedError: Until implemented.
        EscalationRequired: If escalation_clear is missing or mismatches thread.
    """
    raise NotImplementedError("draft not yet implemented")
