"""Tests for throughput metrics computation."""

from clinicloop.world.engine import ItemRecord, RunResult
from clinicloop.world.metrics import compute_snapshot


def test_throughput_on_fixture_log() -> None:
    """For a hand-built fixture log of 3 completed orders spanning 6 simulated hours.

    AC1: throughput.orders_completed == 3 and
         throughput.orders_per_simulated_hour == 0.5
    """
    # Build a fixture with 3 completed orders in 6 simulated hours (360 minutes)
    records = (
        ItemRecord(
            queue="intake",
            item_id="q-001",
            enqueued_at=0,
            started_at=5,
            finished_at=15,
            server=1,
        ),
        ItemRecord(
            queue="prescriber_review",
            item_id="q-001",
            enqueued_at=15,
            started_at=20,
            finished_at=120,
            server=2,
        ),
        ItemRecord(
            queue="pharmacy_fulfilment",
            item_id="o-001",
            enqueued_at=120,
            started_at=125,
            finished_at=135,
            server=3,
        ),
        ItemRecord(
            queue="intake",
            item_id="q-002",
            enqueued_at=60,
            started_at=65,
            finished_at=75,
            server=1,
        ),
        ItemRecord(
            queue="prescriber_review",
            item_id="q-002",
            enqueued_at=75,
            started_at=80,
            finished_at=180,
            server=2,
        ),
        ItemRecord(
            queue="pharmacy_fulfilment",
            item_id="o-002",
            enqueued_at=180,
            started_at=185,
            finished_at=195,
            server=3,
        ),
        ItemRecord(
            queue="intake",
            item_id="q-003",
            enqueued_at=120,
            started_at=125,
            finished_at=135,
            server=1,
        ),
        ItemRecord(
            queue="prescriber_review",
            item_id="q-003",
            enqueued_at=135,
            started_at=140,
            finished_at=240,
            server=2,
        ),
        ItemRecord(
            queue="pharmacy_fulfilment",
            item_id="o-003",
            enqueued_at=240,
            started_at=245,
            finished_at=255,
            server=3,
        ),
    )

    run_result = RunResult(
        records=records,
        queue_depth={
            "intake": ((0, 1), (60, 2), (120, 2), (180, 0), (240, 1), (300, 0), (360, 0)),
            "prescriber_review": ((0, 0), (60, 1), (120, 2), (180, 1), (240, 1), (300, 0), (360, 0)),
            "pharmacy_fulfilment": ((0, 0), (60, 0), (120, 1), (180, 1), (240, 1), (300, 0), (360, 0)),
            "support_inbox": ((0, 0), (60, 0), (120, 0), (180, 0), (240, 0), (300, 0), (360, 0)),
        },
        duration_minutes=360,
        staffing={"intake": 1, "prescriber_review": 4, "pharmacy_fulfilment": 1, "support_inbox": 1},
        run_hash="test_hash_123",
    )

    snapshot = compute_snapshot(run_result)

    assert snapshot.throughput.orders_completed == 3
    assert snapshot.throughput.orders_per_simulated_hour == 0.5
