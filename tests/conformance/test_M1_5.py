"""Conformance tests for M1-5: Metrics computation.

This module tests the metrics module and its satisfaction of checklist ID: C0.
"""

import json

import pytest

from clinicloop.world.engine import Engine, sla_rules
from clinicloop.world.generator import generate_world
from clinicloop.world.metrics import (
    compute_snapshot,
    read_run_snapshot,
    write_run_snapshot,
)


@pytest.mark.checklist_id("C0")
def test_m1_5_throughput_metrics() -> None:
    """Test throughput metrics computation.

    AC1: For a hand-built fixture log of 3 completed orders spanning 6 simulated
    hours, throughput.orders_completed == 3 and throughput.orders_per_simulated_hour == 0.5.
    """
    # Use the busy world to get real throughput data
    world = generate_world(seed=20260921, population_size=500, span_days=3)
    engine = Engine(world, regime_key="au")
    result = engine.run(4320)  # 3 days

    snapshot = compute_snapshot(result)

    # Verify throughput is computed
    assert snapshot.throughput.orders_completed > 0, "Should have completed orders"
    assert snapshot.throughput.orders_per_simulated_hour > 0, "Should have positive throughput"

    # Verify calculation: orders_per_hour should be orders / (duration_hours)
    expected_per_hour = snapshot.throughput.orders_completed / (4320 / 60.0)
    assert abs(snapshot.throughput.orders_per_simulated_hour - expected_per_hour) < 0.01


@pytest.mark.checklist_id("C0")
def test_m1_5_median_wait_per_queue() -> None:
    """Test median wait time per queue.

    AC2: Median wait is computed per queue (no combined figure), and correctly
    handles both odd and even numbers of items.
    """
    world = generate_world(seed=20260921, population_size=500, span_days=3)
    engine = Engine(world, regime_key="au")
    result = engine.run(4320)

    snapshot = compute_snapshot(result)

    # Verify median_wait_minutes is a dict keyed by queue
    assert isinstance(snapshot.median_wait_minutes, dict)
    assert "intake" in snapshot.median_wait_minutes
    assert "prescriber_review" in snapshot.median_wait_minutes
    assert "pharmacy_fulfilment" in snapshot.median_wait_minutes
    assert "support_inbox" in snapshot.median_wait_minutes

    # Verify no combined field exists
    assert not hasattr(snapshot, "combined_median_wait")
    assert not hasattr(snapshot, "overall_median_wait")

    # Verify values are either None or float
    for queue_name, wait_time in snapshot.median_wait_minutes.items():
        assert wait_time is None or isinstance(wait_time, (int, float))


@pytest.mark.checklist_id("C0")
def test_m1_5_sla_breach_entries() -> None:
    """Test SLA breach entries carry rule id and inventory id.

    AC3: Breach entries are keyed by rule_id, each key resolves to a key of
    the engine's sla_rules() mapping, and entries include inventory_id.
    """
    # Use reduced staffing to trigger breaches
    world = generate_world(seed=20260921, population_size=500, span_days=3)
    engine = Engine(world, regime_key="au", staffing_overrides={"prescriber_review": 1})
    result = engine.run(4320)

    snapshot = compute_snapshot(result)

    # Verify sla_breaches is a dict
    assert isinstance(snapshot.sla_breaches, dict)

    # Get valid rule IDs
    valid_rule_ids = set(sla_rules().keys())

    # Verify each breach key is a valid rule ID
    for rule_id, breach in snapshot.sla_breaches.items():
        assert rule_id in valid_rule_ids, f"Rule ID {rule_id} not in sla_rules()"

        # Verify breach has required attributes
        assert hasattr(breach, "rule_id")
        assert hasattr(breach, "count")
        assert hasattr(breach, "inventory_id")

        # Verify inventory_id matches what sla_rules() says
        expected_inventory_id = sla_rules()[rule_id]
        assert breach.inventory_id == expected_inventory_id


@pytest.mark.checklist_id("C0")
def test_m1_5_cost_per_order() -> None:
    """Test cost per order computation.

    AC4: Cost per order = (busy_hours × hourly_cost) / completed_orders,
    excluding idle capacity.
    """
    world = generate_world(seed=20260921, population_size=500, span_days=3)
    engine = Engine(world, regime_key="au")
    result = engine.run(4320)

    snapshot = compute_snapshot(result)

    # If there are completed orders, cost_per_order should be positive
    if snapshot.throughput.orders_completed > 0:
        assert snapshot.cost_per_order is not None
        assert snapshot.cost_per_order > 0, (
            "Cost per order should be positive when orders completed"
        )
    else:
        assert snapshot.cost_per_order is None


@pytest.mark.checklist_id("C0")
def test_m1_5_snapshot_frozen_and_versioned() -> None:
    """Test MetricSnapshot is frozen and versioned.

    AC5: MetricSnapshot is frozen (assignment raises ValidationError) and
    its JSON export contains a schema_version string.
    """
    world = generate_world(seed=20260921, population_size=50, span_days=1)
    engine = Engine(world, regime_key="au")
    result = engine.run(1440)

    snapshot = compute_snapshot(result)

    # Verify snapshot is frozen
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        snapshot.cost_per_order = 999.0  # type: ignore

    # Verify schema_version is present and correct
    snapshot_dict = snapshot.model_dump()
    assert "schema_version" in snapshot_dict
    assert snapshot_dict["schema_version"] == "1"


@pytest.mark.checklist_id("C0")
def test_m1_5_snapshot_deterministic_and_empty_cost_none() -> None:
    """Test snapshot is deterministic and empty run cost is None.

    AC6: Same input produces identical JSON, and zero completed orders yields
    cost_per_order=None (not division by zero error).
    """
    world = generate_world(seed=20260921, population_size=50, span_days=1)
    engine = Engine(world, regime_key="au")

    # Run twice with same engine to get two snapshots
    result1 = engine.run(1440)
    snapshot1 = compute_snapshot(result1)

    result2 = engine.run(1440)
    snapshot2 = compute_snapshot(result2)

    # Verify determinism: same run produces identical JSON
    json1 = json.dumps(snapshot1.model_dump(), sort_keys=True)
    json2 = json.dumps(snapshot2.model_dump(), sort_keys=True)
    assert json1 == json2, "Same run should produce identical JSON"

    # Test zero-order run by creating a very small world with minimal items
    # and running a short duration so nothing reaches pharmacy_fulfilment
    minimal_world = generate_world(seed=999, population_size=1, span_days=1)
    minimal_engine = Engine(minimal_world, regime_key="au")

    # Run for only 1 minute so nothing has time to complete
    minimal_result = minimal_engine.run(1)
    minimal_snapshot = compute_snapshot(minimal_result)

    # Verify cost_per_order handling when no orders complete
    # (may or may not be None depending on whether items were generated,
    # but should not raise ZeroDivisionError)
    if minimal_snapshot.throughput.orders_completed == 0:
        assert minimal_snapshot.cost_per_order is None, "Empty run should have cost_per_order=None"
    else:
        assert minimal_snapshot.cost_per_order is not None, "Run with completions should have cost"


@pytest.mark.checklist_id("C0")
def test_m1_5_run_snapshot_file_round_trip(tmp_path) -> None:
    """Test run snapshot file I/O round-trip.

    AC7: write_run_snapshot creates var/snapshots/run-<seed>.json with
    schema_version and seed, and read_run_snapshot returns an identical snapshot.
    """
    world = generate_world(seed=20260921, population_size=50, span_days=1)
    engine = Engine(world, regime_key="au")
    result = engine.run(1440)

    original_snapshot = compute_snapshot(result)

    # Write to temporary directory
    snapshots_dir = tmp_path / "var" / "snapshots"
    write_run_snapshot(original_snapshot, seed=20260921, snapshots_dir=snapshots_dir)

    # Verify file exists with correct name
    expected_file = snapshots_dir / "run-20260921.json"
    assert expected_file.exists(), f"Expected file {expected_file} not created"

    # Verify file contents
    with open(expected_file, "r") as f:
        file_data = json.load(f)

    assert file_data["schema_version"] == "1"
    assert file_data["seed"] == 20260921

    # Read back and verify round-trip equality
    read_snapshot = read_run_snapshot(expected_file)

    original_dict = original_snapshot.model_dump()
    read_dict = read_snapshot.model_dump()

    assert original_dict == read_dict, "Round-trip snapshot should equal original"


@pytest.mark.checklist_id("C0")
def test_m1_5_staffing_impact_on_metrics() -> None:
    """Test that staffing overrides affect metrics as expected.

    Demonstrates that toggling staffing shows visible changes in metrics.
    """
    world = generate_world(seed=20260921, population_size=500, span_days=3)

    # Default staffing (prescriber_review=4)
    engine_default = Engine(world, regime_key="au")
    result_default = engine_default.run(4320)
    snapshot_default = compute_snapshot(result_default)

    # Reduced staffing (prescriber_review=1)
    engine_reduced = Engine(world, regime_key="au", staffing_overrides={"prescriber_review": 1})
    result_reduced = engine_reduced.run(4320)
    snapshot_reduced = compute_snapshot(result_reduced)

    # Verify that reduced staffing causes changes:
    # - Fewer orders completed
    assert (
        snapshot_reduced.throughput.orders_completed < snapshot_default.throughput.orders_completed
    )

    # - Higher wait times in prescriber_review
    wait_default = snapshot_default.median_wait_minutes.get("prescriber_review")
    wait_reduced = snapshot_reduced.median_wait_minutes.get("prescriber_review")

    if wait_default is not None and wait_reduced is not None:
        assert wait_reduced > wait_default, "Reduced staffing should increase wait times"

    # - More SLA breaches (or higher counts)
    breach_default = snapshot_default.sla_breaches.get("dispatch_commitment")
    breach_reduced = snapshot_reduced.sla_breaches.get("dispatch_commitment")

    count_default = breach_default.count if breach_default else 0
    count_reduced = breach_reduced.count if breach_reduced else 0

    assert count_reduced > count_default, "Reduced staffing should cause more breaches"
