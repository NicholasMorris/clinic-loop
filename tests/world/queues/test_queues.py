"""Tests for queue functionality."""

import pytest

from clinicloop.world.queues import queues


def test_four_queues_record_enqueue_and_dequeue_times() -> None:
    """The engine exposes exactly four named queues with proper timestamps.

    Each queue should record:
    - intake
    - prescriber_review
    - pharmacy_fulfilment
    - support_inbox

    Each item should have:
    - enqueued_at: non-null simulated timestamp
    - dequeued_at: non-null simulated timestamp >= enqueued_at (or None if still waiting)
    """
    queue_dict = queues()

    # Check that we have exactly the four expected queue names
    expected_names = {"intake", "prescriber_review", "pharmacy_fulfilment", "support_inbox"}
    actual_names = set(queue_dict.keys())

    assert actual_names == expected_names, (
        f"Expected queue names {expected_names}, got {actual_names}"
    )

    # Check that each queue can enqueue and dequeue items with timestamps
    for queue_name, queue in queue_dict.items():
        # Enqueue an item at timestamp 100
        queue.enqueue(f"{queue_name}_item_1", 100)

        # Verify the item is in the queue with the correct enqueued_at timestamp
        assert len(queue.items) == 1
        assert queue.items[0].item_id == f"{queue_name}_item_1"
        assert queue.items[0].enqueued_at == 100
        assert queue.items[0].dequeued_at is None

        # Dequeue the item at timestamp 150
        queue.dequeue(f"{queue_name}_item_1", 150)

        # Verify the item now has the dequeued_at timestamp
        assert queue.items[0].dequeued_at == 150
        assert queue.items[0].dequeued_at >= queue.items[0].enqueued_at
