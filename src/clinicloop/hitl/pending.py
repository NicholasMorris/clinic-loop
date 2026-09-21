"""Query interrupted threads from checkpoint database."""


def list_pending(agent_name: str) -> list[str]:
    """List all interrupted threads for an agent.

    Args:
        agent_name: The name of the agent.

    Returns:
        A list of thread IDs that are interrupted and awaiting human input.
    """
    raise NotImplementedError("list_pending not yet implemented")
