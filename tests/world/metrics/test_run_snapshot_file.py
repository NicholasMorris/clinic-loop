"""Tests for run snapshot file I/O."""

import json
from pathlib import Path

from clinicloop.world.engine import ItemRecord, RunResult
from clinicloop.world.metrics import MetricSnapshot, compute_snapshot, read_run_snapshot, write_run_snapshot


def test_run_snapshot_path_and_round_trip(tmp_path: Path) -> None:
    """write_run_snapshot and read_run_snapshot round-trip correctly.

    AC7: write_run_snapshot(snapshot, seed=20260921) creates
         var/snapshots/run-20260921.json containing schema_version == "1"
         and seed == 20260921, and read_run_snapshot of that path returns
         a MetricSnapshot equal to the original.
    """
    # Create a snapshot
    records = (
        ItemRecord(
            queue="intake",
            item_id="q-001",
            enqueued_at=0,
            started_at=5,
            finished_at=15,
            server=1,
        ),
    )

    run_result = RunResult(
        records=records,
        queue_depth={
            "intake": ((0, 1), (60, 0)),
            "prescriber_review": ((0, 0),),
            "pharmacy_fulfilment": ((0, 0),),
            "support_inbox": ((0, 0),),
        },
        duration_minutes=60,
        staffing={"intake": 1, "prescriber_review": 1, "pharmacy_fulfilment": 1, "support_inbox": 1},
        run_hash="test_hash_file",
    )

    snapshot = compute_snapshot(run_result)

    # Write to a test var/snapshots directory
    snapshots_dir = tmp_path / "var" / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    # Write the snapshot
    write_run_snapshot(snapshot, seed=20260921, snapshots_dir=snapshots_dir)

    # Verify the file exists
    expected_file = snapshots_dir / "run-20260921.json"
    assert expected_file.exists(), f"Expected file {expected_file} not found"

    # Verify file contents
    with open(expected_file, "r") as f:
        file_data = json.load(f)

    assert file_data["schema_version"] == "1"
    assert file_data["seed"] == 20260921

    # Read it back
    read_snapshot = read_run_snapshot(expected_file)

    # Verify round-trip equality
    original_dict = snapshot.model_dump()
    read_dict = read_snapshot.model_dump()

    assert original_dict == read_dict, "Round-trip snapshot should be identical to original"
