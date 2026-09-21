"""Query interrupted threads from checkpoint database."""

import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver

from clinicloop.hitl.checkpoint import checkpoint_root
from clinicloop.hitl.registry import UnknownAgentGraph, get_graph_builder


def list_pending(agent_name: str) -> list[str]:
    """List all interrupted threads for an agent.

    Args:
        agent_name: The name of the agent.

    Returns:
        A list of thread IDs that are interrupted and awaiting human input.
    """
    root = checkpoint_root()
    db_path = root / f"{agent_name}.sqlite"

    # If the database doesn't exist yet, return empty list
    if not db_path.exists():
        return []

    pending_threads: list[str] = []

    try:
        conn = sqlite3.connect(str(db_path), check_same_thread=False)

        # Try to get the graph builder
        try:
            builder = get_graph_builder(agent_name)
        except UnknownAgentGraph:
            conn.close()
            return []

        # Build the graph with the checkpointer
        graph = builder(checkpointer=SqliteSaver(conn))

        # Query distinct thread_ids
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id")
        thread_ids = [row[0] for row in cursor.fetchall()]

        # For each thread, check if it's pending
        for thread_id in thread_ids:
            state = graph.get_state({"configurable": {"thread_id": thread_id}})

            # A thread is pending iff state.next is non-empty AND
            # "human_decision" not in state.values
            if state.next and "human_decision" not in state.values:
                pending_threads.append(thread_id)

        conn.close()
    except (sqlite3.OperationalError, Exception):
        # Database error
        pass

    return pending_threads
