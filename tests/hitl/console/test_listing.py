"""Tests for listing pending items from checkpoint databases."""

import sqlite3
from pathlib import Path

import pytest
from langgraph.checkpoint.sqlite import SqliteSaver

from clinicloop.hitl.console.backend import list_pending
from clinicloop.hitl.reference_graph import build_reference_graph
from clinicloop.hitl.registry import register_graph


@pytest.fixture
def checkpoint_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a checkpoint root with test databases.

    Creates two agent databases each with one interrupted thread,
    and a third database outside the root.
    """
    root = tmp_path / "checkpoints"
    root.mkdir(parents=True, exist_ok=True)

    # Monkeypatch the environment variable
    monkeypatch.setenv("CLINICLOOP_CHECKPOINT_ROOT", str(root))

    # Register the reference-b graph builder
    register_graph("reference-b", build_reference_graph)

    # Create first agent database with one interrupted thread
    db1_path = root / "reference.sqlite"
    conn1 = sqlite3.connect(str(db1_path), check_same_thread=False)
    graph1 = build_reference_graph(checkpointer=SqliteSaver(conn1))
    config1 = {"configurable": {"thread_id": "case_001"}}
    graph1.invoke({"case_id": "case_001"}, config1)
    conn1.close()

    # Create second agent database with one interrupted thread
    db2_path = root / "reference-b.sqlite"
    conn2 = sqlite3.connect(str(db2_path), check_same_thread=False)
    graph2 = build_reference_graph(checkpointer=SqliteSaver(conn2))
    config2 = {"configurable": {"thread_id": "case_002"}}
    graph2.invoke({"case_id": "case_002"}, config2)
    conn2.close()

    # Create a third database outside the root to verify isolation
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir(parents=True, exist_ok=True)
    db3_path = outside_dir / "reference.sqlite"
    conn3 = sqlite3.connect(str(db3_path), check_same_thread=False)
    graph3 = build_reference_graph(checkpointer=SqliteSaver(conn3))
    config3 = {"configurable": {"thread_id": "case_003"}}
    graph3.invoke({"case_id": "case_003"}, config3)
    conn3.close()

    return root


def test_lists_pending_items_from_configured_root_only(
    checkpoint_root: Path,
) -> None:
    """AC1: list_pending returns two items from root, not the outside database.

    The two items should be ordered by interruption timestamp ascending,
    and the outside database should not appear in the result.
    """
    listing = list_pending()

    # Should have exactly two items from the configured root
    assert len(listing.items) == 2
    assert len(listing.errors) == 0

    # Verify items have required fields
    for item in listing.items:
        assert item.agent is not None
        assert item.case_id is not None
        assert item.node is not None
        assert item.payload is not None
        assert item.interrupted_at is not None

    # Verify order by interrupted_at ascending
    assert listing.items[0].interrupted_at <= listing.items[1].interrupted_at


def test_unreadable_database_does_not_hide_other_agents(
    checkpoint_root: Path,
    tmp_path: Path,
) -> None:
    """AC5: Unreadable database reports error; other agents still return items.

    A database that is missing or garbage yields a ConsoleSourceError,
    while the good databases still return their pending items.
    """
    # Create a garbage file where an agent database should be
    garbage_path = checkpoint_root / "garbage.sqlite"
    garbage_path.write_bytes(b"not a valid sqlite database")

    listing = list_pending()

    # Should have the two good items
    assert len(listing.items) == 2

    # Should have one error for the garbage file
    assert len(listing.errors) == 1
    assert listing.errors[0].agent == "garbage"
    assert listing.errors[0].message is not None
