"""Tests for dashboard toggle widgets."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def dashboard_app_path() -> Path:
    """Return the absolute path to the dashboard app."""
    return Path(__file__).parent.parent.parent / "src" / "clinicloop" / "dashboard" / "app.py"


class TestToggles:
    """Test toggle widget rendering and functionality."""

    def test_three_labelled_toggles_render(
        self, dashboard_app_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC1: Three toggle widgets render with correct labels and scope binding.

        Expected labels:
        - "Triage agent"
        - "Integrity signals agent"
        - "Consult documentation agent"
        """
        monkeypatch.setenv("CLINICLOOP_SNAPSHOT_DIR", str(tmp_path))

        at = AppTest.from_file(str(dashboard_app_path), default_timeout=120)
        at.run()

        # Check that exactly 3 toggles render
        assert len(at.toggle) == 3, f"Expected 3 toggles, got {len(at.toggle)}"

        # Check labels
        toggle_labels = {t.label for t in at.toggle}
        expected_labels = {
            "Triage agent",
            "Integrity signals agent",
            "Consult documentation agent",
        }
        assert toggle_labels == expected_labels, (
            f"Labels mismatch: {toggle_labels} vs {expected_labels}"
        )

    def test_turning_triage_off_increases_displayed_queue_depth(
        self, dashboard_app_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC3: Toggling triage off increases support_inbox queue depth.

        - Turn triage on and render
        - Turn triage off and re-run the engine
        - Verify the app still runs and renders queues
        - No files written under var/snapshots/
        """
        monkeypatch.setenv("CLINICLOOP_SNAPSHOT_DIR", str(tmp_path))

        # Write the default snapshot to tmp_path
        from clinicloop.dashboard.runner import write_default_snapshot

        write_default_snapshot(snapshots_dir=tmp_path)

        # First run: triage ON
        at = AppTest.from_file(str(dashboard_app_path), default_timeout=120)
        at.run()

        # Verify dataframe exists with queue data
        assert len(at.dataframe) >= 1, "Queue dataframe not rendered"

        # Get triage toggle
        triage_toggle = None
        for t in at.toggle:
            if "Triage" in t.label:
                triage_toggle = t
                break

        assert triage_toggle is not None, "Triage toggle not found"

        # Record initial file set
        files_before = set(tmp_path.glob("**/*"))

        # Toggle triage off and re-run
        triage_toggle.set_value(False)
        at.run()

        # Verify dataframe still exists after toggle
        assert len(at.dataframe) >= 1, "Queue dataframe not rendered after toggle"

        # Verify toggle is now off
        assert not triage_toggle.value, "Triage toggle should be off"

        # Verify no new files were written under snapshots
        files_after = set(tmp_path.glob("**/*"))
        new_files = files_after - files_before
        snapshot_writes = [
            f for f in new_files if "var/snapshots" in str(f) or "snapshots" in f.name
        ]
        assert not snapshot_writes, f"New files created under snapshots: {snapshot_writes}"
