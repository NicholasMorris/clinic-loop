"""Tests for listing pending interrupted threads."""

import sqlite3
from pathlib import Path

import pytest
from langgraph.checkpoint.sqlite import SqliteSaver

from clinicloop.hitl.pending import list_pending
from clinicloop.hitl.reference_graph import build_reference_graph


def test_list_pending_returns_only_interrupted_threads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """list_pending returns only thread ids of interrupted threads.

    Should return thread IDs that are currently interrupted and awaiting
    human input, and omit threads that ran to completion.
    """
    root = tmp_path / "checkpoints"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("CLINICLOOP_CHECKPOINT_ROOT", str(root))

    # Create an interrupted thread
    db_path = root / "reference.sqlite"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    graph = build_reference_graph(checkpointer=SqliteSaver(conn))
    config = {"configurable": {"thread_id": "interrupted_case"}}
    graph.invoke({"case_id": "interrupted_case"}, config)

    # Create a completed thread by running to completion
    # First update the state to clear the human_decision channel
    # (simulating that a decision was already made)
    config2 = {"configurable": {"thread_id": "completed_case"}}
    graph.invoke({"case_id": "completed_case"}, config2)
    graph.update_state(config2, {"human_decision": {"kind": "approve", "actor": "test"}})

    conn.close()

    # Get pending threads for the reference agent
    pending = list_pending("reference")

    # Should return only the interrupted case, not the completed one
    assert isinstance(pending, list)
    assert len(pending) == 1
    assert pending[0] == "interrupted_case"
