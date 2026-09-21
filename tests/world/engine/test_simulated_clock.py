"""Tests for simulated clock independence from wall clock."""

from unittest.mock import patch

import pytest

from clinicloop.world.engine import Engine
from clinicloop.world.generator import generate_world
from clinicloop.world.regimes import RegimeParameterNotSet, get_regime


def test_engine_never_reads_wall_clock() -> None:
    """Verify the engine uses only simulated time, not wall-clock time.

    The engine should complete a 24-hour run without reading:
    - time.time()
    - time.monotonic()

    When these are patched to raise AssertionError, the engine should
    succeed without calling them.
    """

    def wall_clock_blocker(*args: object, **kwargs: object) -> None:
        """Raise error if wall-clock functions are called."""
        raise AssertionError("Engine called a wall-clock time function")

    # Patch wall-clock functions (datetime.now can't be patched directly due to immutability)
    with (
        patch("time.time", side_effect=wall_clock_blocker),
        patch("time.monotonic", side_effect=wall_clock_blocker),
    ):
        # Generate a world and run the engine
        world = generate_world(
            seed=789,
            population_size=50,
            span_days=1,
        )

        engine = Engine(world, regime_key="au")
        engine.run(1440)  # 24 hours

        # If we reach here, the engine didn't read the wall clock
        hash_value = engine.run_hash()
        assert isinstance(hash_value, str)


def test_nz_regime_raises_not_set_error() -> None:
    """Verify that accessing NZ regime parameters raises RegimeParameterNotSet.

    The NZ regime is a placeholder with no parameters populated.
    """
    nz_regime = get_regime("nz")

    # Attempting to read a parameter should raise RegimeParameterNotSet
    with pytest.raises(RegimeParameterNotSet):
        _ = nz_regime.dispatch_commitment_business_days

    # Attempting to run the engine with NZ regime should also raise this
    world = generate_world(
        seed=999,
        population_size=50,
        span_days=1,
    )

    engine = Engine(world, regime_key="nz")

    # The engine.run() should raise when it tries to access regime parameters
    with pytest.raises(RegimeParameterNotSet):
        engine.run(1440)
