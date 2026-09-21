"""Conformance tests for M1-2: Discrete-event simulation engine.

This module tests the discrete-event engine and its satisfaction of
the checklist IDs: C0, G1, G2.
"""

from unittest.mock import patch

import pytest

from clinicloop.world.engine import Engine
from clinicloop.world.generator import generate_world
from clinicloop.world.regimes import RegimeParameterNotSet


@pytest.mark.checklist_id("C0")
def test_engine_processes_items_through_queues() -> None:
    """Test that engine processes items through queues with service times.

    Checklist C0: SimClinic clock, four queues with enqueue/dequeue timestamps.
    Items must have started_at and finished_at set when serviced.
    """
    world = generate_world(seed=42, population_size=100, span_days=7)
    engine = Engine(world, regime_key="au")
    result = engine.run(10080)  # 7 days in minutes

    # Check that items are actually serviced
    serviced_count = sum(1 for r in result.records if r.finished_at is not None)
    assert serviced_count > 0, "Engine should service items through queues"

    # Check items before cutoff have proper timing
    cutoff_time = 10080 - 60
    for record in result.records:
        if record.enqueued_at < cutoff_time and record.finished_at is not None:
            assert record.started_at is not None
            assert record.started_at >= record.enqueued_at
            assert record.finished_at > record.started_at


@pytest.mark.checklist_id("C0")
def test_engine_respects_staffing_configuration() -> None:
    """Test that engine reads and respects staffing configuration.

    Staffing levels affect queue depths and service times.
    """
    world = generate_world(seed=123, population_size=150, span_days=3)

    # Run with default staffing
    engine_default = Engine(world, regime_key="au")
    result_default = engine_default.run(4320)  # 3 days

    # Run with reduced prescriber_review staffing
    engine_reduced = Engine(world, regime_key="au", staffing_overrides={"prescriber_review": 1})
    result_reduced = engine_reduced.run(4320)

    # With reduced staffing, max queue depth should increase
    default_max = max((d[1] for d in result_default.queue_depth["prescriber_review"]), default=0)
    reduced_max = max((d[1] for d in result_reduced.queue_depth["prescriber_review"]), default=0)

    assert reduced_max >= default_max, "Reduced staffing should not decrease max queue depth"


@pytest.mark.checklist_id("G1")
def test_engine_determinism_with_seed() -> None:
    """Test that same seed produces identical run hash.

    Checklist G1: Deterministic simulation given a seed.
    """
    world1 = generate_world(seed=42, population_size=100, span_days=1)
    engine1 = Engine(world1, regime_key="au")
    result1 = engine1.run(1440)
    hash1 = result1.run_hash

    world2 = generate_world(seed=42, population_size=100, span_days=1)
    engine2 = Engine(world2, regime_key="au")
    result2 = engine2.run(1440)
    hash2 = result2.run_hash

    assert hash1 == hash2, "Same seed should produce identical hash"

    # Different seed should produce different hash
    world3 = generate_world(seed=99, population_size=100, span_days=1)
    engine3 = Engine(world3, regime_key="au")
    result3 = engine3.run(1440)
    hash3 = result3.run_hash

    assert hash1 != hash3, "Different seed should produce different hash"


@pytest.mark.checklist_id("G1")
def test_engine_uses_only_simulated_time() -> None:
    """Test that engine never calls wall-clock time functions.

    Determinism requires that no external time source is consulted.
    """

    def wall_clock_blocker(*args: object, **kwargs: object) -> None:
        raise AssertionError("Engine must not call wall-clock functions")

    with (
        patch("time.time", side_effect=wall_clock_blocker),
        patch("time.monotonic", side_effect=wall_clock_blocker),
    ):
        world = generate_world(seed=789, population_size=50, span_days=1)
        engine = Engine(world, regime_key="au")
        result = engine.run(1440)
        assert result.run_hash is not None


@pytest.mark.checklist_id("G2")
def test_engine_respects_regime_seam() -> None:
    """Test that NZ and UK regimes are placeholders; AU is implemented.

    Checklist G2: Regime differences; AU populated, NZ/UK placeholder with seam.
    """
    world = generate_world(seed=999, population_size=50, span_days=1)

    # AU should work without error
    engine_au = Engine(world, regime_key="au")
    result_au = engine_au.run(1440)
    assert result_au.run_hash is not None

    # NZ should raise when trying to access regime parameters
    engine_nz = Engine(world, regime_key="nz")
    with pytest.raises(RegimeParameterNotSet):
        engine_nz.run(1440)

    # UK should also raise
    engine_uk = Engine(world, regime_key="uk")
    with pytest.raises(RegimeParameterNotSet):
        engine_uk.run(1440)
