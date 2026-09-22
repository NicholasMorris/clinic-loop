"""Node wrappers for the triage graph.

Each wrapper is a closure that binds extra arguments (model, tools, ruleset, etc.)
to the M2-5a node functions, creating a function of (state, config) -> dict[str, Any]
that LangGraph can call.
"""

from typing import Any

EXPECTED_NODES = frozenset([
    "ingest",
    "classify_intent",
    "escalation_check",
    "resolve",
    "draft",
    "regulatory_guard",
    "human_approval",
    "guard_final",
    "send",
    "human_review",
    "escalate",
])


def make_ingest_node(message_source, run_key: str):
    """Create ingest node closure.

    Args:
        message_source: MessageSource implementation.
        run_key: Key for consistent hashing.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """
    raise NotImplementedError


def make_classify_intent_node(model):
    """Create classify_intent node closure.

    Args:
        model: ModelPort with complete() method.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """
    raise NotImplementedError


def make_escalation_check_node(ruleset, classifier=None):
    """Create escalation_check node closure.

    Args:
        ruleset: Ruleset object.
        classifier: Optional classifier callable.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """
    raise NotImplementedError


def make_resolve_node(model, tools, timeout_seconds: float = 5.0):
    """Create resolve node closure with timeout.

    Args:
        model: ModelPort with complete() method.
        tools: ToolRunner protocol.
        timeout_seconds: Timeout for tool execution.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """
    raise NotImplementedError


def make_draft_node(model):
    """Create draft node closure.

    Args:
        model: ModelPort with complete() method.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """
    raise NotImplementedError


def make_regulatory_guard_node(ruleset):
    """Create regulatory_guard node closure.

    Args:
        ruleset: Ruleset object.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """
    raise NotImplementedError


def human_approval_node(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Human approval node (pure pass-through).

    The interrupt happens at compile time via interrupt_before.
    On resume, this node just lets routing proceed.

    Args:
        state: Current state.
        config: Config dict.

    Returns:
        Empty dict (routing determined by human_decision in state).
    """
    raise NotImplementedError


def make_guard_final_node(ruleset):
    """Create guard_final node closure.

    Args:
        ruleset: Ruleset object.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """
    raise NotImplementedError


def make_send_node(outbound_port):
    """Create send node closure.

    Args:
        outbound_port: OutboundPort implementation.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """
    raise NotImplementedError


def human_review_node(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Human review node (pure pass-through).

    Args:
        state: Current state.
        config: Config dict.

    Returns:
        Empty dict.
    """
    raise NotImplementedError


def escalate_node(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Escalate node (pure pass-through).

    Args:
        state: Current state.
        config: Config dict.

    Returns:
        Empty dict.
    """
    raise NotImplementedError
