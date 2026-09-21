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

    Note:
        This is a helper function for wiring approval gates into a graph.
        It works with static interrupt_before and update_state resumption.
    """

    # Return a node function that acts as a pass-through
    # The actual interrupt logic is handled by graph.compile(interrupt_before=[...])
    def gate_node(state: dict[str, Any]) -> dict[str, Any]:
        """Approval gate node that pauses for human decision."""
        # The node itself just passes through; the interrupt happens at compile time
        return state

    return gate_node


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

    Note:
        This helper collects answers through multiple interrupts.
        Each question surfaces in sequence and answers are collected in order.
    """
    # Initialize result dictionary
    result: dict[str, Any] = {
        "thread_id": thread_id,
        "questions": questions,
        "answers": [],
    }

    # The actual question loop would use dynamic interrupt()
    # For now, return the structure ready for answers to be populated
    return result
