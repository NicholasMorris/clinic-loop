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
    engine1.run(1440)
    hash1 = engine1.run_hash()

    # Generate another world with the same seed and run it
    world2 = generate_world(
        seed=42,
        population_size=50,
        span_days=1,
    )
    engine2 = Engine(world2, regime_key="au")
    engine2.run(1440)
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
    engine3.run(1440)
    hash3 = engine3.run_hash()

    # Different seed should produce a different hash
    assert hash1 != hash3, "Different seed should produce different run hashes"
