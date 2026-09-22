"""Classify intent node: determine intent from patient message."""


def classify_intent(state: dict, model) -> dict:  # type: ignore[no-untyped-def]
    """Classify inbound message intent.

    Args:
        state: Current TriageState as dict.
        model: ModelPort with complete(prompt, *, sample_index=0) method.

    Returns:
        State update dict with intent field.

    Raises:
        NotImplementedError: Until implemented.
    """
    raise NotImplementedError("classify_intent not yet implemented")
