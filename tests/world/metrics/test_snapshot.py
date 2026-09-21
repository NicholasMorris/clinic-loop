"""Tests for MetricSnapshot model."""

import json

import pytest
from pydantic import ValidationError

from clinicloop.world.engine import ItemRecord, RunResult
from clinicloop.world.metrics import compute_snapshot


def test_snapshot_is_frozen_and_versioned() -> None:
    """MetricSnapshot is frozen and exports a schema_version.

    AC5: MetricSnapshot is frozen (assignment raises pydantic.ValidationError)
         and its JSON export contains a schema_version string.
    """
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
        staffing={
            "intake": 1,
            "prescriber_review": 1,
            "pharmacy_fulfilment": 1,
            "support_inbox": 1,
        },
        run_hash="test_hash",
    )

    snapshot = compute_snapshot(run_result)

    # Verify snapshot is frozen (direct assignment to snapshot field fails)
    with pytest.raises(ValidationError):
        snapshot.cost_per_order = 999.0  # type: ignore

    # Verify JSON export contains schema_version
    snapshot_dict = snapshot.model_dump()
    assert "schema_version" in snapshot_dict
    assert isinstance(snapshot_dict["schema_version"], str)
    assert snapshot_dict["schema_version"] == "1"


def test_snapshot_is_deterministic_and_empty_run_cost_is_none() -> None:
    """Computing a snapshot twice from same log produces identical JSON.

    AC6: Computing a snapshot twice from the same event log produces equal
         JSON exports, and a run with zero completed orders yields
         cost_per_order is None rather than raising ZeroDivisionError.
    """
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
        staffing={
            "intake": 1,
            "prescriber_review": 1,
            "pharmacy_fulfilment": 1,
            "support_inbox": 1,
        },
        run_hash="test_hash_determinism",
    )

    # Compute twice
    snapshot1 = compute_snapshot(run_result)
    snapshot2 = compute_snapshot(run_result)

    # JSON should be identical
    json1 = json.dumps(snapshot1.model_dump(), sort_keys=True)
    json2 = json.dumps(snapshot2.model_dump(), sort_keys=True)

    assert json1 == json2, "Snapshots from same log should produce identical JSON"

    # Test empty run (no pharmacy_fulfilment completions = zero orders dispatched)
    empty_records = (
        ItemRecord(
            queue="intake",
            item_id="q-001",
            enqueued_at=0,
            started_at=None,
            finished_at=None,
            server=None,
        ),
    )

    empty_run_result = RunResult(
        records=empty_records,
        queue_depth={
            "intake": ((0, 1), (60, 1)),
            "prescriber_review": ((0, 0),),
            "pharmacy_fulfilment": ((0, 0),),
            "support_inbox": ((0, 0),),
        },
        duration_minutes=60,
        staffing={
            "intake": 1,
            "prescriber_review": 1,
            "pharmacy_fulfilment": 1,
            "support_inbox": 1,
        },
        run_hash="test_hash_empty",
    )

    empty_snapshot = compute_snapshot(empty_run_result)

    # Should not raise ZeroDivisionError; cost_per_order should be None
    assert empty_snapshot.cost_per_order is None, (
        "Cost per order should be None for zero completed orders"
    )
