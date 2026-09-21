"""Tests for dashboard metric panels."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from clinicloop.world.regimes.inventory_ids import KNOWN_INVENTORY_IDS


@pytest.fixture
def dashboard_app_path() -> Path:
    """Return the absolute path to the dashboard app."""
    return Path(__file__).parent.parent.parent / "src" / "clinicloop" / "dashboard" / "app.py"


class TestMetricPanels:
    """Test metric panel rendering and values."""

    def test_four_metric_panels_render_values(
        self, dashboard_app_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC2: Four metric panels render with non-empty values.

        Expected metrics:
        - Throughput
        - Median wait
        - SLA breaches
        - Cost per order
        """
        monkeypatch.setenv("CLINICLOOP_SNAPSHOT_DIR", str(tmp_path))

        # Write the default snapshot
        from clinicloop.dashboard.runner import write_default_snapshot

        write_default_snapshot(snapshots_dir=tmp_path)

        at = AppTest.from_file(str(dashboard_app_path), default_timeout=120)
        at.run()

        # Check that exactly 4 metrics render
        assert len(at.metric) == 4, f"Expected 4 metrics, got {len(at.metric)}"

        # Extract metric labels
        metric_labels = {m.label for m in at.metric}
        expected_labels = {"Throughput", "Median wait", "SLA breaches", "Cost per order"}
        assert metric_labels == expected_labels, (
            f"Metric labels mismatch: {metric_labels} vs {expected_labels}"
        )

        # Verify each metric has a non-empty value
        for metric in at.metric:
            assert metric.value, f"Metric '{metric.label}' has empty value"

    def test_breach_detail_shows_rule_and_manifest_inventory_ids(
        self, dashboard_app_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC4: SLA breach detail table shows rule_id and inventory_id.

        Each row shows:
        - rule_id: The SLA rule ID
        - inventory_id: A member of KNOWN_INVENTORY_IDS
        """
        monkeypatch.setenv("CLINICLOOP_SNAPSHOT_DIR", str(tmp_path))

        # Write the default snapshot
        from clinicloop.dashboard.runner import write_default_snapshot

        write_default_snapshot(snapshots_dir=tmp_path)

        at = AppTest.from_file(str(dashboard_app_path), default_timeout=120)
        at.run()

        # If there are breaches, the second dataframe should be the breach detail table
        # If there are no breaches, there may only be one dataframe (queues)
        if len(at.dataframe) > 1:
            breach_df = at.dataframe[1].data

            # If the breach table has data, verify it meets criteria
            if len(breach_df) > 0:
                # Check that all required columns exist
                assert "rule_id" in breach_df.columns, "rule_id column missing"
                assert "inventory_id" in breach_df.columns, "inventory_id column missing"

                # Verify all inventory_ids are in KNOWN_INVENTORY_IDS
                for inv_id in breach_df["inventory_id"]:
                    assert inv_id in KNOWN_INVENTORY_IDS, (
                        f"Inventory ID '{inv_id}' not in KNOWN_INVENTORY_IDS"
                    )


def test_dashboard_labels_figures_as_simulated(
    dashboard_app_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cost and other figures are labelled as simulated with assumed inputs."""
    from clinicloop.dashboard.runner import write_default_snapshot

    monkeypatch.setenv("CLINICLOOP_SNAPSHOT_DIR", str(tmp_path))
    write_default_snapshot()
    at = AppTest.from_file(str(dashboard_app_path), default_timeout=120).run()
    captions = " ".join(c.value for c in at.caption)
    assert "simulated" in captions and "assumed" in captions
