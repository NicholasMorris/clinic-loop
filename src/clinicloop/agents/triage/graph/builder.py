"""Build the triage graph."""

from typing import Any, Optional


def build_triage_graph(
    *,
    model: Any,
    tools: Any,
    ruleset: Any,
    message_source: Any,
    outbound_port: Any,
    classifier: Optional[Any] = None,
    run_key: str = "triage",
    timeout_seconds: float = 5.0,
    checkpointer: Optional[Any] = None,
) -> Any:
    """Build and compile the triage LangGraph.

    Args:
        model: ModelPort with complete() method.
        tools: ToolRunner protocol.
        ruleset: Ruleset object.
        message_source: MessageSource implementation.
        outbound_port: OutboundPort implementation.
        classifier: Optional escalation classifier.
        run_key: Key for consistent hashing.
        timeout_seconds: Timeout for tool execution.
        checkpointer: Optional SqliteSaver for checkpointing.

    Returns:
        A compiled LangGraph StateGraph with interrupt_before=['human_approval'].
    """
    raise NotImplementedError
