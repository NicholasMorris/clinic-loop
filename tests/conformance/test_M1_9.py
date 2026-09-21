"""Conformance tests for M1-9: review console.

Checklist ID: C0
"""

import sqlite3
from pathlib import Path

import pytest
from langgraph.checkpoint.sqlite import SqliteSaver

from clinicloop.hitl.console.backend import apply_decision, list_pending
from clinicloop.hitl.console.errors import DecisionAlreadyRecorded
from clinicloop.hitl.decision import HumanDecision
from clinicloop.hitl.reference_graph import build_reference_graph
from clinicloop.hitl.registry import register_graph


@pytest.mark.checklist_id("C0")
def test_review_console_workflow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """C0: Review console lists and applies decisions to pending items.

    End-to-end workflow: create interrupted threads, list them,
    apply decisions, and verify they are no longer pending.
    """
    root = tmp_path / "checkpoints"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("CLINICLOOP_CHECKPOINT_ROOT", str(root))

    # Register the reference graph
    register_graph("reference", build_reference_graph)

    # Create an interrupted thread
    db_path = root / "reference.sqlite"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    graph = build_reference_graph(checkpointer=SqliteSaver(conn))
    config = {"configurable": {"thread_id": "case_001"}}
    graph.invoke({"case_id": "case_001"}, config)
    conn.close()

    # List pending items
    listing = list_pending()
    assert len(listing.items) == 1
    assert len(listing.errors) == 0

    item = listing.items[0]
    assert item.agent == "reference"
    assert item.case_id == "case_001"
    assert item.node == "human_approval"
    assert item.payload["case_id"] == "case_001"

    # Apply an approval decision
    decision = apply_decision(
        agent="reference",
        case_id="case_001",
        kind="approve",
        reviewer="dr_alice",
    )

    assert decision["kind"] == "approve"
    assert decision["actor"] == "dr_alice"
    assert decision["decided_at"] is not None

    # Verify the item is no longer pending
    listing_after = list_pending()
    assert len(listing_after.items) == 0

    # Verify the decision was recorded by constructing a HumanDecision
    decision_obj = HumanDecision(
        action=decision["kind"],
        decided_by=decision["actor"],
        decided_at=decision["decided_at"],
    )
    assert decision_obj.action == "approve"
    assert decision_obj.decided_by == "dr_alice"


@pytest.mark.checklist_id("C0")
def test_review_console_edit_preserves_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """C0: Edit decision stores edited text byte-for-byte.

    Edited text is applied unchanged with unicode and trailing newlines preserved.
    """
    root = tmp_path / "checkpoints"
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("CLINICLOOP_CHECKPOINT_ROOT", str(root))

    register_graph("reference", build_reference_graph)

    db_path = root / "reference.sqlite"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    graph = build_reference_graph(checkpointer=SqliteSaver(conn))
    config = {"configurable": {"thread_id": "case_edit"}}
    graph.invoke({"case_id": "case_edit"}, config)
    conn.close()

    # Apply an edit with unicode and newline
    edited = "Modified text with unicode: café\n"
    decision = apply_decision(
        agent="reference",
        case_id="case_edit",
        kind="edit",
        reviewer="dr_bob",
        edited_text=edited,
    )

    assert decision["edited_text"] == edited
    assert decision["edited_text"].endswith("\n")

    # Verify the decision cannot be applied twice
    with pytest.raises(DecisionAlreadyRecorded):
        apply_decision(
            agent="reference",
            case_id="case_edit",
            kind="reject",
            reviewer="dr_charlie",
            reason="should fail",
        )
