"""Tests for median wait metrics computation."""

from clinicloop.world.engine import ItemRecord, RunResult
from clinicloop.world.metrics import compute_snapshot


def test_median_wait_matches_hand_computed_values() -> None:
    """For fixture queues with known waits, median_wait is correctly computed.

    AC2: For a queue with waits of 10, 20 and 60 simulated minutes,
         median_wait_minutes["intake"] == 20.0
         For an even-sized fixture with waits 10, 20, 30 and 60 it equals 25.0
         The snapshot exposes no combined across-queue median field.
    """
    # Fixture 1: Odd number (3 items) with waits 10, 20, 60 -> median 20
    records_odd = (
        ItemRecord(
            queue="intake",
            item_id="q-001",
            enqueued_at=0,
            started_at=10,
            finished_at=20,
            server=1,
        ),
        ItemRecord(
            queue="intake",
            item_id="q-002",
            enqueued_at=5,
            started_at=25,
            finished_at=45,
            server=1,
        ),
        ItemRecord(
            queue="intake",
            item_id="q-003",
            enqueued_at=10,
            started_at=70,
            finished_at=120,
            server=1,
        ),
    )

    run_result_odd = RunResult(
        records=records_odd,
        queue_depth={
            "intake": ((0, 1), (60, 2), (120, 1), (180, 0)),
            "prescriber_review": ((0, 0),),
            "pharmacy_fulfilment": ((0, 0),),
            "support_inbox": ((0, 0),),
        },
        duration_minutes=180,
        staffing={"intake": 1, "prescriber_review": 1, "pharmacy_fulfilment": 1, "support_inbox": 1},
        run_hash="test_hash_odd",
    )

    snapshot_odd = compute_snapshot(run_result_odd)

    # For odd number of items: (10, 20, 60) -> sorted is (10, 20, 60) -> median is 20
    assert snapshot_odd.median_wait_minutes["intake"] == 20.0
    assert "prescriber_review" not in snapshot_odd.median_wait_minutes or snapshot_odd.median_wait_minutes["prescriber_review"] is None

    # Check no combined median field exists
    assert not hasattr(snapshot_odd, "combined_median_wait_minutes")
    assert not hasattr(snapshot_odd, "overall_median_wait_minutes")

    # Fixture 2: Even number (4 items) with waits 10, 20, 30, 60 -> median 25
    records_even = (
        ItemRecord(
            queue="intake",
            item_id="q-001",
            enqueued_at=0,
            started_at=10,
            finished_at=20,
            server=1,
        ),
        ItemRecord(
            queue="intake",
            item_id="q-002",
            enqueued_at=5,
            started_at=25,
            finished_at=45,
            server=1,
        ),
        ItemRecord(
            queue="intake",
            item_id="q-003",
            enqueued_at=10,
            started_at=40,
            finished_at=70,
            server=1,
        ),
        ItemRecord(
            queue="intake",
            item_id="q-004",
            enqueued_at=15,
            started_at=75,
            finished_at=135,
            server=1,
        ),
    )

    run_result_even = RunResult(
        records=records_even,
        queue_depth={
            "intake": ((0, 1), (60, 2), (120, 1), (180, 0)),
            "prescriber_review": ((0, 0),),
            "pharmacy_fulfilment": ((0, 0),),
            "support_inbox": ((0, 0),),
        },
        duration_minutes=180,
        staffing={"intake": 1, "prescriber_review": 1, "pharmacy_fulfilment": 1, "support_inbox": 1},
        run_hash="test_hash_even",
    )

    snapshot_even = compute_snapshot(run_result_even)

    # For even number of items: (10, 20, 30, 60) -> sorted -> median is (20+30)/2 = 25.0
    assert snapshot_even.median_wait_minutes["intake"] == 25.0
