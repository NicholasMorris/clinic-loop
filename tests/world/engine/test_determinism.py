"""Tests for deterministic run hash generation."""

from clinicloop.world.engine import Engine
from clinicloop.world.generator import generate_world


def test_run_hash_stable_across_runs(tmp_path: str) -> None:
    """Two runs with the same seed should produce identical run_hash values.

    This test verifies that the event loop is deterministic and reproducible.
    Different seeds should produce different hashes.
    """
    # Generate a world with seed 42
    world1 = generate_world(
        seed=42,
        population_size=50,
        span_days=1,
    )

    # Run the engine for 1440 minutes (24 hours)
    engine1 = Engine(world1, regime_key="au")
    result1 = engine1.run(1440)
    hash1 = engine1.run_hash()

    # Generate another world with the same seed and run it
    world2 = generate_world(
        seed=42,
        population_size=50,
        span_days=1,
    )
    engine2 = Engine(world2, regime_key="au")
    result2 = engine2.run(1440)
    hash2 = engine2.run_hash()

    # Same seed should produce the same hash
    assert hash1 == hash2, "Same seed should produce identical run hashes"

    # Generate a world with a different seed
    world3 = generate_world(
        seed=99,
        population_size=50,
        span_days=1,
    )
    engine3 = Engine(world3, regime_key="au")
    result3 = engine3.run(1440)
    hash3 = engine3.run_hash()

    # Different seed should produce a different hash
    assert hash1 != hash3, "Different seed should produce different run hashes"


def test_items_actually_get_serviced() -> None:
    """Verify that items arriving before duration-60 are actually served.

    Items must have started_at >= enqueued_at and finished_at > started_at.
    This test should fail against the hollow engine that only enqueues.
    """
    world = generate_world(
        seed=42,
        population_size=100,
        span_days=30,
    )

    engine = Engine(world, regime_key="au")
    result = engine.run(43200)  # 30 days in minutes

    # Check that items arriving before duration-60 are actually served
    duration_minus_60 = 43200 - 60
    for record in result.records:
        if record.enqueued_at < duration_minus_60:
            # Item should have been started and finished
            assert record.started_at is not None, (
                f"Item {record.item_id} in queue {record.queue} "
                "enqueued before cutoff should have started_at"
            )
            assert record.finished_at is not None, (
                f"Item {record.item_id} in queue {record.queue} "
                "enqueued before cutoff should have finished_at"
            )
            assert record.started_at >= record.enqueued_at, (
                f"Item {record.item_id}: started_at must be >= enqueued_at"
            )
            assert record.finished_at > record.started_at, (
                f"Item {record.item_id}: finished_at must be > started_at"
            )


def test_staffing_override_affects_hash() -> None:
    """Verify that staffing overrides change the run hash.

    Different staffing levels should produce different hashes due to
    different service time patterns.
    """
    world = generate_world(
        seed=555,
        population_size=50,
        span_days=1,
    )

    engine1 = Engine(world, regime_key="au")
    result1 = engine1.run(1440)
    hash1 = engine1.run_hash()

    # Run with a staffing override (reduce prescriber_review staff to 1)
    engine2 = Engine(world, regime_key="au", staffing_overrides={"prescriber_review": 1})
    result2 = engine2.run(1440)
    hash2 = engine2.run_hash()

    # Different staffing levels should produce different hashes
    assert hash1 != hash2, (
        "Different staffing levels should produce different run hashes"
    )
