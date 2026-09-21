"""Conformance test for M1-7: the dashboard is the metrics surface only (C0)."""

import ast
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from clinicloop.dashboard.runner import write_default_snapshot

DASHBOARD_DIR = Path(__file__).parent.parent.parent / "src" / "clinicloop" / "dashboard"


@pytest.mark.checklist_id("C0")
def test_dashboard_is_metrics_surface_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exactly four metrics and three toggles render, and no review-console code is imported."""
    monkeypatch.setenv("CLINICLOOP_SNAPSHOT_DIR", str(tmp_path))
    write_default_snapshot()
    at = AppTest.from_file(str(DASHBOARD_DIR / "app.py"), default_timeout=120).run()
    assert not at.exception
    assert len(at.metric) == 4
    assert len(at.toggle) == 3

    for module in DASHBOARD_DIR.glob("*.py"):
        for node in ast.walk(ast.parse(module.read_text())):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            assert not any("hitl" in name for name in names), f"{module.name} imports {names}"
