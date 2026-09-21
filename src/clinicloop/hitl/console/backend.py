"""Backend for the review console."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Sequence

from clinicloop.hitl.checkpoint import checkpoint_root
from clinicloop.hitl.console.errors import (
    ConsoleSourceError,
    DecisionAlreadyRecorded,
    UnknownDecisionKind,
)
from clinicloop.hitl.registry import UnknownAgentGraph, get_graph_builder


@dataclass(frozen=True)
class PendingItem:
    """A pending item awaiting human decision.

    Attributes:
        agent: The agent name.
        case_id: The case identifier.
        node: The interrupted node name.
        payload: The state payload dict.
        interrupted_at: ISO string timestamp of interruption.
    """

    agent: str
    case_id: str
    node: str
    payload: dict[str, Any]
    interrupted_at: str


@dataclass(frozen=True)
class PendingListing:
    """A listing of pending items and any errors.

    Attributes:
        items: List of pending items.
        errors: List of source errors encountered.
    """

    items: list[PendingItem]
    errors: list[ConsoleSourceError]


def list_pending(agents: Sequence[str] | None = None) -> PendingListing:
    """List pending items from checkpoint databases.

    Args:
        agents: Sequence of agent names to query, or None to query all.
            If None, discovers all *.sqlite files under checkpoint_root().

    Returns:
        A PendingListing with items and errors.
    """
    root = checkpoint_root()
    items: list[PendingItem] = []
    errors: list[ConsoleSourceError] = []

    # Determine which agents to query
    if agents is None:
        # Discover all *.sqlite files directly under the root
        if not root.exists():
            return PendingListing(items=[], errors=[])
        agent_files = sorted(root.glob("*.sqlite"))
        agents_to_query = [f.stem for f in agent_files]
    else:
        agents_to_query = list(agents)

    # Query each agent
    for agent_name in agents_to_query:
        try:
            db_path = root / f"{agent_name}.sqlite"

            # Check if file exists
            if not db_path.exists():
                errors.append(
                    ConsoleSourceError(
                        agent=agent_name,
                        message=f"Database file not found: {db_path}",
                    )
                )
                continue

            # Open the database
            conn = sqlite3.connect(str(db_path), check_same_thread=False)

            try:
                # Try to get the graph builder
                try:
                    builder = get_graph_builder(agent_name)
                except UnknownAgentGraph:
                    errors.append(
                        ConsoleSourceError(
                            agent=agent_name,
                            message=f"No registered graph builder for agent '{agent_name}'",
                        )
                    )
                    continue

                # Build the graph with the checkpointer
                from langgraph.checkpoint.sqlite import SqliteSaver

                graph = builder(checkpointer=SqliteSaver(conn))

                # Query distinct thread_ids
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id")
                thread_ids = [row[0] for row in cursor.fetchall()]

                # For each thread, check if it's pending
                for thread_id in thread_ids:
                    state = graph.get_state({"configurable": {"thread_id": thread_id}})

                    # An item is pending iff state.next is non-empty AND
                    # "human_decision" not in state.values
                    if state.next and "human_decision" not in state.values:
                        item = PendingItem(
                            agent=agent_name,
                            case_id=thread_id,
                            node=state.next[0],
                            payload=dict(state.values),
                            interrupted_at=state.created_at,
                        )
                        items.append(item)

            finally:
                conn.close()

        except sqlite3.DatabaseError as e:
            errors.append(
                ConsoleSourceError(
                    agent=agent_name,
                    message=f"Database error: {e}",
                )
            )
        except Exception as e:
            errors.append(
                ConsoleSourceError(
                    agent=agent_name,
                    message=f"Error querying agent: {e}",
                )
            )

    # Sort items by interrupted_at, then agent, then case_id
    items.sort(key=lambda x: (x.interrupted_at, x.agent, x.case_id))

    return PendingListing(items=items, errors=errors)


def apply_decision(
    agent: str,
    case_id: str,
    kind: str,
    reviewer: str,
    *,
    edited_text: str | None = None,
    reason: str | None = None,
    clock: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    """Apply a human decision to a pending item.

    Args:
        agent: The agent name.
        case_id: The case identifier.
        kind: The decision kind ("approve", "edit", or "reject").
        reviewer: The reviewer identifier.
        edited_text: Optional edited text when kind is "edit".
        reason: Optional reason when kind is "reject".
        clock: Optional clock function returning datetime (default: now).

    Returns:
        The recorded decision dict.

    Raises:
        UnknownDecisionKind: If kind is not one of the known values.
        DecisionAlreadyRecorded: If a decision is already recorded.
    """
    # Validate kind
    if kind not in ("approve", "edit", "reject"):
        raise UnknownDecisionKind(f"Unknown decision kind: {kind}")

    # Validate edit requires edited_text
    if kind == "edit" and not edited_text:
        raise ValueError("edited_text is required when kind is 'edit'")

    # Get the checkpoint root and build the graph
    root = checkpoint_root()
    db_path = root / f"{agent}.sqlite"

    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver

        builder = get_graph_builder(agent)
        graph = builder(checkpointer=SqliteSaver(conn))

        config = {"configurable": {"thread_id": case_id}}
        state = graph.get_state(config)

        # Check if a decision is already recorded
        if "human_decision" in state.values:
            raise DecisionAlreadyRecorded(
                f"A decision has already been recorded for {agent}:{case_id}"
            )

        # Prepare the decision dict
        clock_fn = clock if clock else lambda: datetime.now(timezone.utc)
        decided_at = clock_fn().isoformat()

        decision_dict: dict[str, Any] = {
            "kind": kind,
            "actor": reviewer,
            "decided_at": decided_at,
        }

        if kind == "edit" and edited_text is not None:
            decision_dict["edited_text"] = edited_text
        if kind == "reject" and reason is not None:
            decision_dict["reason"] = reason

        # Update state with the decision
        graph.update_state(config, {"human_decision": decision_dict})

        return decision_dict

    finally:
        conn.close()
