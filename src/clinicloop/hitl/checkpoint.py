"""Checkpointing support for LangGraph agents."""

from langgraph.checkpoint.sqlite import SqliteSaver


def build_checkpointer(agent_name: str) -> SqliteSaver:
    """Build a SQLite checkpointer for an agent.

    Args:
        agent_name: The name of the agent (used for the database filename).

    Returns:
        A SqliteSaver configured at var/checkpoints/<agent_name>.sqlite
        with thread_id set to case id.
    """
    raise NotImplementedError("build_checkpointer not yet implemented")
