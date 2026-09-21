"""Pure simulation runner for dashboard (no streamlit imports)."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from clinicloop.world.generator import generate_world
from clinicloop.world.engine import Engine
from clinicloop.world.metrics import compute_snapshot, MetricSnapshot, write_run_snapshot
from clinicloop.world.ports import PortRegistry, FakeAgentPort


# Configuration constants
SEED = 20260921
POPULATION = 500
SPAN_DAYS = 3
DURATION_MINUTES = 4320

# Mapping of scope names to engine agent toggle keys
SCOPE_TO_ENGINE = {
    "triage": "triage",
    "integrity": "integrity",
    "consult_documentation": "consult_scribe",
}


def snapshot_dir() -> Path:
    """Get the snapshot directory path.

    Returns:
        Path to snapshots directory, defaulting to var/snapshots.
    """
    return Path(os.environ.get("CLINICLOOP_SNAPSHOT_DIR", "var/snapshots"))


def snapshot_path() -> Path:
    """Get the default snapshot file path.

    Returns:
        Path to run-{SEED}.json file.
    """
    return snapshot_dir() / f"run-{SEED}.json"


def build_registry() -> PortRegistry:
    """Build a PortRegistry with FakeAgentPort on each toggleable scope.

    Returns:
        A PortRegistry with FakeAgentPort(service_time_fraction=0.1) on each
        toggleable scope (triage, integrity, consult_documentation).
    """
    registry = PortRegistry()
    for scope in registry.toggleable_scopes():
        registry.register(scope, FakeAgentPort(service_time_fraction=0.1))
    return registry


@lru_cache(maxsize=1)
def _get_cached_world() -> Any:
    """Get a cached world instance.

    Returns:
        A World object generated with SEED, POPULATION, and SPAN_DAYS.
    """
    return generate_world(seed=SEED, population_size=POPULATION, span_days=SPAN_DAYS)


def run_with_toggles(toggles: dict[str, bool]) -> tuple[MetricSnapshot, dict[str, int]]:
    """Run the engine with specified toggle states and return metrics.

    This function:
    - Generates a world (cached)
    - Creates an Engine with the specified agent toggles
    - Runs for DURATION_MINUTES
    - Computes and returns MetricSnapshot and max queue depths
    - Writes no file, reads no file (except the cached world)

    Args:
        toggles: Dictionary mapping scope name to boolean (e.g. {"triage": False, ...})

    Returns:
        Tuple of (MetricSnapshot, dict[queue_name -> max_depth]).
    """
    world = _get_cached_world()

    # Convert scope names to engine agent names
    agent_toggles = {SCOPE_TO_ENGINE[scope]: value for scope, value in toggles.items()}

    # Run the engine
    engine = Engine(world, regime_key="au", agent_toggles=agent_toggles)
    run_result = engine.run(DURATION_MINUTES)

    # Compute snapshot
    snapshot = compute_snapshot(run_result)

    # Extract max queue depth from queue_depth data
    max_depths: dict[str, int] = {}
    for queue_name, depth_samples in run_result.queue_depth.items():
        if depth_samples:
            max_depths[queue_name] = max(depth for timestamp, depth in depth_samples)
        else:
            max_depths[queue_name] = 0

    return snapshot, max_depths


def write_default_snapshot(snapshot_dir: Path | str | None = None) -> None:
    """Write default snapshot with all toggles on.

    Args:
        snapshot_dir: Directory to write snapshot to. Defaults to env var or var/snapshots.
    """
    if snapshot_dir is None:
        snapshot_dir = snapshot_dir()
    else:
        snapshot_dir = Path(snapshot_dir)

    # All toggles on
    toggles = {scope: True for scope in ["triage", "integrity", "consult_documentation"]}

    # Run with all toggles on
    snapshot, _ = run_with_toggles(toggles)

    # Write to file
    write_run_snapshot(snapshot, SEED, snapshot_dir)
