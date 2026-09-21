"""Tests for dashboard toggle widgets."""

import os
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
        assert toggle_labels == expected_labels, f"Labels mismatch: {toggle_labels} vs {expected_labels}"

    def test_turning_triage_off_increases_displayed_queue_depth(
        self, dashboard_app_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC3: Toggling triage off increases support_inbox queue depth.

        - Turn triage on, record support_inbox max_queue_depth
        - Turn triage off, compare max_queue_depth
        - Off state must be strictly greater than on state
        - No files written under var/snapshots/
        """
        monkeypatch.setenv("CLINICLOOP_SNAPSHOT_DIR", str(tmp_path))

        # Write the default snapshot to tmp_path
        from clinicloop.dashboard.runner import write_default_snapshot

        write_default_snapshot(snapshot_dir=tmp_path)

        # First run: triage ON
        at = AppTest.from_file(str(dashboard_app_path), default_timeout=120)
        at.run()

        # Get the dataframe with queue metrics
        queue_df = None
        for df in at.dataframe:
            if "queue" in str(df.columns):
                queue_df = df
                break

        assert queue_df is not None, "Queue dataframe not found"

        # Find support_inbox row and get max_queue_depth when triage is on
        support_inbox_row_on = queue_df[queue_df["queue"] == "support_inbox"]
        assert len(support_inbox_row_on) > 0, "support_inbox row not found when triage is on"
        depth_on = support_inbox_row_on["max_queue_depth"].iloc[0]

        # Second run: turn triage OFF
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

        # Get queue depth when triage is off
        queue_df_off = None
        for df in at.dataframe:
            if "queue" in str(df.columns):
                queue_df_off = df
                break

        assert queue_df_off is not None, "Queue dataframe not found after toggle"

        support_inbox_row_off = queue_df_off[queue_df_off["queue"] == "support_inbox"]
        assert len(support_inbox_row_off) > 0, "support_inbox row not found when triage is off"
        depth_off = support_inbox_row_off["max_queue_depth"].iloc[0]

        # When triage is off, queue depth should be strictly greater
        assert depth_off > depth_on, (
            f"Expected queue depth to increase when triage is off: "
            f"off={depth_off} should be > on={depth_on}"
        )

        # Verify no new files were written under snapshots
        files_after = set(tmp_path.glob("**/*"))
        new_files = files_after - files_before
        snapshot_writes = [f for f in new_files if "var/snapshots" in str(f) or "snapshots" in f.name]
        assert not snapshot_writes, f"New files created under snapshots: {snapshot_writes}"
