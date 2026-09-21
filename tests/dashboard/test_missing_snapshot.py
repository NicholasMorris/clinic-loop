"""Tests for missing snapshot handling."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def dashboard_app_path() -> Path:
    """Return the absolute path to the dashboard app."""
    return Path(__file__).parent.parent.parent / "src" / "clinicloop" / "dashboard" / "app.py"


class TestMissingSnapshot:
    """Test behavior when snapshot file is missing."""

    def test_missing_snapshot_renders_make_target_instruction(
        self, dashboard_app_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC6: Missing snapshot renders 'make sim-snapshot' instruction.

        When var/snapshots/run-20260921.json does not exist:
        - App renders st.info() with literal text "make sim-snapshot"
        - No exception is raised
        """
        monkeypatch.setenv("CLINICLOOP_SNAPSHOT_DIR", str(tmp_path))

        # Ensure tmp_path is empty (no snapshot file)
        assert not list(tmp_path.glob("**/*")), "tmp_path should be empty"

        at = AppTest.from_file(str(dashboard_app_path), default_timeout=120)
        at.run()

        # Check that the info message was rendered
        info_messages = at.info
        assert len(info_messages) > 0, "No info message rendered"

        # Check that at least one info message contains "make sim-snapshot"
        found = False
        for info in info_messages:
            if "make sim-snapshot" in str(info.value):
                found = True
                break

        assert found, (
            f"'make sim-snapshot' not found in info messages. "
            f"Messages: {[str(i.value) for i in info_messages]}"
        )
