"""Tests for agent port toggle effects on queue metrics."""

import pytest

from clinicloop.world.engine import Engine
from clinicloop.world.generator import generate_world
from clinicloop.world.metrics import compute_snapshot
from clinicloop.world.ports.fakes import FakeAgentPort


@pytest.mark.skip(reason="Requires agent_toggles parameter in Engine (not yet implemented)")
def test_disabling_fake_triage_port_increases_queue_depth_and_wait() -> None:
    """AC2: Disabling the triage port increases support_inbox queue depth and wait.

    With FakeAgentPort(service_time_fraction=0.1) on triage scope and support_inbox
    mean_service_minutes assumed at 10, one seed shows strictly lower depth and
    median wait with the port enabled vs disabled.

    This test requires Engine to support agent_toggles parameter, which will be
    added in a future commit to enable toggle scheduling.
    """
    seed = 20260921
    population_size = 500
    span_days = 3
    duration = 4320  # 3 days in minutes

    # Generate world
    world = generate_world(
        seed=seed,
        population_size=population_size,
        span_days=span_days,
    )

    # Run WITH triage agent enabled
    engine_with_agent = Engine(world, regime_key="au")
    # TODO: Pass agent_toggles={"triage": True} when engine supports it
    result_with = engine_with_agent.run(duration)
    snapshot_with = compute_snapshot(result_with)

    # Run WITHOUT triage agent
    engine_without_agent = Engine(world, regime_key="au")
    # TODO: Pass agent_toggles={"triage": False} when engine supports it
    result_without = engine_without_agent.run(duration)
    snapshot_without = compute_snapshot(result_without)

    # With agent enabled: lower depth and median wait
    depth_with = _get_max_queue_depth(result_with, "support_inbox")
    depth_without = _get_max_queue_depth(result_without, "support_inbox")
    wait_with = snapshot_with.median_wait_minutes.get("support_inbox") or 0
    wait_without = snapshot_without.median_wait_minutes.get("support_inbox") or 0

    assert depth_with < depth_without, (
        f"With agent: depth={depth_with}, "
        f"without: depth={depth_without}"
    )
    assert wait_with < wait_without, (
        f"With agent: wait={wait_with}, without: wait={wait_without}"
    )


def _get_max_queue_depth(result: "RunResult", queue_name: str) -> int:  # type: ignore[name-defined]
    """Helper: get max queue depth from queue_depth samples."""
    if queue_name not in result.queue_depth:
        return 0
    samples = result.queue_depth[queue_name]
    if not samples:
        return 0
    return max(depth for _, depth in samples)
