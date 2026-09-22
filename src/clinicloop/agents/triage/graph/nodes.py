"""Node wrappers for the triage graph.

Each wrapper is a closure that binds extra arguments (model, tools, ruleset, etc.)
to the M2-5a node functions, creating a function of (state, config) -> dict[str, Any]
that LangGraph can call.
"""

import concurrent.futures
from typing import Any, Callable, Optional

from clinicloop.agents.triage.nodes.classify_intent import classify_intent
from clinicloop.agents.triage.nodes.draft import draft
from clinicloop.agents.triage.nodes.guard_final import guard_final
from clinicloop.agents.triage.nodes.ingest import ingest
from clinicloop.agents.triage.nodes.regulatory_guard import regulatory_guard
from clinicloop.agents.triage.nodes.resolve import resolve
from clinicloop.compliance.escalation.detector import detect

EXPECTED_NODES = frozenset(
    [
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
    ]
)


def make_ingest_node(
    message_source: Any, run_key: str
) -> Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]:
    """Create ingest node closure.

    Args:
        message_source: MessageSource implementation.
        run_key: Key for consistent hashing.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """

    def ingest_node(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Ingest node wrapper that fetches the raw message.

        The raw message is never stored in state or config; only the
        message_id goes through config['configurable'].
        """
        message_id = config.get("configurable", {}).get("message_id", "")
        raw_message = message_source.fetch(message_id)
        return ingest(state, raw_message, run_key)

    return ingest_node


def make_classify_intent_node(
    model: Any,
) -> Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]:
    """Create classify_intent node closure.

    Args:
        model: ModelPort with complete() method.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """

    def classify_intent_node(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Classify intent node wrapper."""
        return classify_intent(state, model)

    return classify_intent_node


def make_escalation_check_node(
    ruleset: Any, classifier: Optional[Callable[[list[dict[str, str]]], Optional[str]]] = None
) -> Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]:
    """Create escalation_check node closure.

    Args:
        ruleset: Ruleset object.
        classifier: Optional classifier callable.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """

    def escalation_check_node(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Escalation check node wrapper."""
        # Convert thread to dict format
        redacted_thread = state.get("redacted_thread", [])
        thread_dicts = [
            {"role": turn.get("role"), "text": turn.get("text")} for turn in redacted_thread
        ]

        # Run escalation detection
        result = detect(thread_dicts, ruleset, classifier=classifier)

        return {
            "escalation_category": result.category,
            "escalation_clear": result.clear,
        }

    return escalation_check_node


def make_resolve_node(
    model: Any, tools: Any, timeout_seconds: float = 5.0
) -> Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]:
    """Create resolve node closure with timeout.

    Args:
        model: ModelPort with complete() method.
        tools: ToolRunner protocol.
        timeout_seconds: Timeout for tool execution.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """

    def resolve_node(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Resolve node wrapper with timeout."""
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(resolve, state, model, tools)
                try:
                    return future.result(timeout=timeout_seconds)
                except concurrent.futures.TimeoutError:
                    return {"routing_reason": "tool_timeout"}
                finally:
                    executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            # Any other exception: re-raise for visibility
            raise

    return resolve_node


def make_draft_node(model: Any) -> Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]:
    """Create draft node closure.

    Args:
        model: ModelPort with complete() method.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """

    def draft_node(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Draft node wrapper."""
        return draft(state, model)

    return draft_node


def make_regulatory_guard_node(
    ruleset: Any,
) -> Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]:
    """Create regulatory_guard node closure.

    Args:
        ruleset: Ruleset object.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """

    def regulatory_guard_node(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Regulatory guard node wrapper."""
        return regulatory_guard(state, ruleset)

    return regulatory_guard_node


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
    return {}


def make_guard_final_node(
    ruleset: Any,
) -> Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]:
    """Create guard_final node closure.

    Args:
        ruleset: Ruleset object.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """

    def guard_final_node(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Guard final node wrapper."""
        return guard_final(state, ruleset)

    return guard_final_node


def make_send_node(
    outbound_port: Any,
) -> Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]:
    """Create send node closure.

    Args:
        outbound_port: OutboundPort implementation.

    Returns:
        Function of (state, config) -> dict[str, Any].
    """

    def send_node(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        """Send node wrapper."""
        # Determine final text based on human decision
        human_decision = state.get("human_decision")
        if human_decision and human_decision.action == "edit":
            final_text = human_decision.edited_text
        else:
            final_text = state.get("draft", "")

        # Get final verdict (the last one from guard_final)
        guard_verdicts = state.get("guard_verdicts", [])
        if guard_verdicts:
            final_verdict = guard_verdicts[-1]
        else:
            raise ValueError("send node requires a guard verdict")

        # Send through the port
        outbound_port.send(final_text, final_verdict)

        return {}

    return send_node


def human_review_node(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Human review node (pure pass-through).

    Args:
        state: Current state.
        config: Config dict.

    Returns:
        Empty dict.
    """
    return {}


def escalate_node(state: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Escalate node (pure pass-through).

    Args:
        state: Current state.
        config: Config dict.

    Returns:
        Empty dict.
    """
    return {}
