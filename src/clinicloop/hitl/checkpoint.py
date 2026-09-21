"""Checkpointing support for LangGraph agents."""

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


def build_checkpointer(agent_name: str) -> SqliteSaver:
    """Build a SQLite checkpointer for an agent.

    Args:
        agent_name: The name of the agent (used for the database filename).

    Returns:
        A SqliteSaver configured at var/checkpoints/<agent_name>.sqlite
        with thread_id set to case id.
    """
    # Create checkpoints directory if it doesn't exist
    checkpoint_dir = Path("var") / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # Create the database path
    db_path = str(checkpoint_dir / f"{agent_name}.sqlite")

    # Create a connection to the database
    conn = sqlite3.connect(db_path)

    # Create and return the saver
    return SqliteSaver(conn)
