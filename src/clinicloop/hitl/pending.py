"""Query interrupted threads from checkpoint database."""

import sqlite3
from pathlib import Path


def list_pending(agent_name: str) -> list[str]:
    """List all interrupted threads for an agent.

    Args:
        agent_name: The name of the agent.

    Returns:
        A list of thread IDs that are interrupted and awaiting human input.
    """
    db_path = Path("var") / "checkpoints" / f"{agent_name}.sqlite"

    # If the database doesn't exist yet, return empty list
    if not db_path.exists():
        return []

    pending_threads: list[str] = []

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Query for threads that have pending interrupts
        # The checkpoint database stores interrupt information
        cursor.execute(
            """
            SELECT DISTINCT thread_id FROM checkpoint
            WHERE next IS NOT NULL AND next != ''
            ORDER BY thread_id
            """
        )

        pending_threads = [row[0] for row in cursor.fetchall()]
        conn.close()
    except (sqlite3.OperationalError, Exception):
        # Database not yet initialized or other error
        pass

    return pending_threads
