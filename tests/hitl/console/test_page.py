"""AppTest smoke test for the review console page against a real interrupted graph."""

import sqlite3
from pathlib import Path

import pytest
from langgraph.checkpoint.sqlite import SqliteSaver
from streamlit.testing.v1 import AppTest

from clinicloop.hitl import build_reference_graph

PAGE = (
    Path(__file__).parent.parent.parent.parent
    / "src"
    / "clinicloop"
    / "hitl"
    / "console"
    / "page.py"
)


def _interrupt_thread(root: Path, case_id: str) -> None:
    conn = sqlite3.connect(root / "reference.sqlite", check_same_thread=False)
    graph = build_reference_graph(checkpointer=SqliteSaver(conn))
    graph.invoke({"case_id": case_id}, {"configurable": {"thread_id": case_id}})
    conn.close()


def test_page_lists_then_clears_item_after_decision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One pending row is shown; applying an approve leaves the listing empty."""
    monkeypatch.setenv("CLINICLOOP_CHECKPOINT_ROOT", str(tmp_path))
    _interrupt_thread(tmp_path, "case-page-1")

    at = AppTest.from_file(str(PAGE), default_timeout=60).run()
    assert not at.exception
    assert len(at.dataframe[0].value) == 1
    assert at.selectbox(key="selected_item").value == "reference/case-page-1"

    at.text_input(key="reviewer_id").set_value("dr-test")
    at.button[0].click().run()
    assert not at.exception
    assert "Decision recorded for reference/case-page-1." in [s.value for s in at.success]
    assert [i.value for i in at.info] == ["No pending items awaiting review."]


def test_page_requires_reviewer_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Clicking Apply without a reviewer id shows an error and records nothing."""
    monkeypatch.setenv("CLINICLOOP_CHECKPOINT_ROOT", str(tmp_path))
    _interrupt_thread(tmp_path, "case-page-2")

    at = AppTest.from_file(str(PAGE), default_timeout=60).run()
    at.button[0].click().run()
    assert [e.value for e in at.error] == ["Reviewer ID is required."]
    assert len(at.dataframe[0].value) == 1
