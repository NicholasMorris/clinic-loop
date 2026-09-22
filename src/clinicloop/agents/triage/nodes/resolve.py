"""Resolve node: call tools for certain intents."""


def resolve(state: dict, model, tools) -> dict:  # type: ignore[no-untyped-def]
    """Call tools for order-related intents (order_status, cancellation, delivery_problem).

    For other intents, returns empty update.

    Args:
        state: Current TriageState as dict.
        model: ModelPort with complete(prompt, *, sample_index=0) method.
        tools: ToolRunner protocol with run(name, patient_id, order_id) -> str.

    Returns:
        State update dict with tool_calls list (empty if intent doesn't need tools).

    Raises:
        NotImplementedError: Until implemented.
    """
    raise NotImplementedError("resolve not yet implemented")
