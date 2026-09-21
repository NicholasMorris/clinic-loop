"""Tests for applying decisions to pending items."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from clinicloop.hitl.console.backend import apply_decision, list_pending
from clinicloop.hitl.console.errors import DecisionAlreadyRecorded, UnknownDecisionKind
from clinicloop.hitl.decision import HumanDecision
from clinicloop.hitl.reference_graph import build_reference_graph
from langgraph.checkpoint.sqlite import SqliteSaver


@pytest.fixture
def checkpoint_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a checkpoint root with one interrupted thread."""
    root = tmp_path / "checkpoints"
    root.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("CLINICLOOP_CHECKPOINT_ROOT", str(root))

    # Create agent database with one interrupted thread
    db_path = root / "reference.sqlite"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    graph = build_reference_graph(checkpointer=SqliteSaver(conn))
    config = {"configurable": {"thread_id": "case_001"}}
    graph.invoke({"case_id": "case_001"}, config)
    conn.close()

    return root


def test_approve_records_actor_and_clears_pending(
    checkpoint_root: Path,
) -> None:
    """AC2: apply_decision with approve records actor/timestamp and clears pending.

    After approving, the item should no longer appear in list_pending().
    """
    # Initially one item is pending
    listing_before = list_pending()
    assert len(listing_before.items) == 1

    # Apply approve decision
    recorded = apply_decision(
        agent="reference",
        case_id="case_001",
        kind="approve",
        reviewer="dr_alice",
    )

    # Verify the recorded decision has actor and timestamp
    assert recorded["kind"] == "approve"
    assert recorded["actor"] == "dr_alice"
    assert recorded["decided_at"] is not None

    # Verify the item no longer appears in pending
    listing_after = list_pending()
    assert len(listing_after.items) == 0


def test_three_decision_kinds_accepted_others_rejected(
    checkpoint_root: Path,
) -> None:
    """AC3: approve, edit, reject accepted; others raise UnknownDecisionKind.

    Edit requires edited_text (byte-for-byte), reject stores reason,
    others raise UnknownDecisionKind.
    """
    # Test approve
    recorded = apply_decision(
        agent="reference",
        case_id="case_001",
        kind="approve",
        reviewer="dr_bob",
    )
    assert recorded["kind"] == "approve"

    # Create another interrupted case for edit/reject tests
    checkpoint_root_path = Path(checkpoint_root)
    db_path = checkpoint_root_path / "reference.sqlite"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    graph = build_reference_graph(checkpointer=SqliteSaver(conn))
    config = {"configurable": {"thread_id": "case_002"}}
    graph.invoke({"case_id": "case_002"}, config)
    conn.close()

    # Test edit
    recorded_edit = apply_decision(
        agent="reference",
        case_id="case_002",
        kind="edit",
        reviewer="dr_charlie",
        edited_text="edited payload",
    )
    assert recorded_edit["kind"] == "edit"
    assert recorded_edit["edited_text"] == "edited payload"

    # Create another for reject test
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    graph = build_reference_graph(checkpointer=SqliteSaver(conn))
    config = {"configurable": {"thread_id": "case_003"}}
    graph.invoke({"case_id": "case_003"}, config)
    conn.close()

    # Test reject
    recorded_reject = apply_decision(
        agent="reference",
        case_id="case_003",
        kind="reject",
        reviewer="dr_diana",
        reason="requires further review",
    )
    assert recorded_reject["kind"] == "reject"
    assert recorded_reject["reason"] == "requires further review"

    # Test invalid kind raises UnknownDecisionKind
    with pytest.raises(UnknownDecisionKind):
        apply_decision(
            agent="reference",
            case_id="case_001",
            kind="invalid",  # type: ignore
            reviewer="someone",
        )


def test_second_decision_is_refused(
    checkpoint_root: Path,
) -> None:
    """AC4: Second apply_decision raises DecisionAlreadyRecorded, first unchanged.

    Calling apply_decision twice for the same case raises on the second call
    and does not overwrite the first decision.
    """
    # Apply first decision
    recorded_first = apply_decision(
        agent="reference",
        case_id="case_001",
        kind="approve",
        reviewer="dr_first",
    )

    # Attempting second decision raises
    with pytest.raises(DecisionAlreadyRecorded):
        apply_decision(
            agent="reference",
            case_id="case_001",
            kind="reject",
            reviewer="dr_second",
            reason="different reason",
        )

    # Verify the first decision is unchanged
    checkpoint_root_path = Path(checkpoint_root)
    db_path = checkpoint_root_path / "reference.sqlite"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    graph = build_reference_graph(checkpointer=SqliteSaver(conn))
    config = {"configurable": {"thread_id": "case_001"}}
    state = graph.get_state(config)
    assert state.values.get("human_decision", {}).get("actor") == "dr_first"
    assert state.values.get("human_decision", {}).get("kind") == "approve"
    conn.close()
