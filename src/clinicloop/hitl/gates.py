"""Approval gates and question loops for human-in-the-loop workflows."""

from typing import Any


def approval_gate(
    node_name: str,
    target_node: str,
) -> Any:
    """Wire an approval gate with static interrupt_before.

    Args:
        node_name: The name of the approval gate node.
        target_node: The name of the target node after approval.

    Returns:
        A configured approval gate node.
    """
    raise NotImplementedError("approval_gate not yet implemented")


def question_loop(
    questions: list[str],
    thread_id: str,
) -> dict[str, Any]:
    """Build a dynamic interrupt() question loop.

    Args:
        questions: List of questions to ask.
        thread_id: The thread ID for the conversation.

    Returns:
        A dictionary with collected answers indexed by question.
    """
    raise NotImplementedError("question_loop not yet implemented")
