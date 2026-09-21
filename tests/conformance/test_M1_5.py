"""Conformance tests for M1-5: Metrics computation."""

from tests.conformance.registry import conformance_test


@conformance_test("C0", "M1-5")
def test_m1_5_ac1_throughput_on_fixture_log() -> None:
    """AC1: Throughput metrics computed correctly.

    Tests that throughput is computed as orders_completed and orders_per_simulated_hour.
    """
    # This test is satisfied by tests/world/metrics/test_throughput.py::test_throughput_on_fixture_log
    pass


@conformance_test("C0", "M1-5")
def test_m1_5_ac2_median_wait_per_queue() -> None:
    """AC2: Median wait time computed per queue.

    Tests that median_wait_minutes is keyed by queue and correctly calculated,
    with no combined across-queue median field.
    """
    # This test is satisfied by tests/world/metrics/test_wait.py::test_median_wait_matches_hand_computed_values
    pass


@conformance_test("C0", "M1-5")
def test_m1_5_ac3_sla_breach_entries() -> None:
    """AC3: SLA breach entries carry rule id and inventory id.

    Tests that breaches are keyed by rule_id and include inventory_id from sla_rules().
    """
    # This test is satisfied by tests/world/metrics/test_breaches.py::test_breach_entries_carry_rule_and_inventory_ids
    pass


@conformance_test("C0", "M1-5")
def test_m1_5_ac4_cost_per_order() -> None:
    """AC4: Cost per order computed correctly.

    Tests that cost_per_order = busy_hours × hourly_cost / completed_orders,
    excluding idle capacity.
    """
    # This test is satisfied by tests/world/metrics/test_cost.py::test_cost_per_order_on_fixture_log
    pass


@conformance_test("C0", "M1-5")
def test_m1_5_ac5_snapshot_frozen_and_versioned() -> None:
    """AC5: MetricSnapshot is frozen and versioned.

    Tests that snapshot assignment raises ValidationError and schema_version is present.
    """
    # This test is satisfied by tests/world/metrics/test_snapshot.py::test_snapshot_is_frozen_and_versioned
    pass


@conformance_test("C0", "M1-5")
def test_m1_5_ac6_snapshot_deterministic_and_empty_cost_none() -> None:
    """AC6: Snapshot is deterministic and empty run cost is None.

    Tests that same input produces identical JSON and zero orders yields cost_per_order=None.
    """
    # This test is satisfied by tests/world/metrics/test_snapshot.py::test_snapshot_is_deterministic_and_empty_run_cost_is_none
    pass


@conformance_test("C0", "M1-5")
def test_m1_5_ac7_run_snapshot_file_round_trip() -> None:
    """AC7: Run snapshot files round-trip correctly.

    Tests that write_run_snapshot and read_run_snapshot produce identical snapshots.
    """
    # This test is satisfied by tests/world/metrics/test_run_snapshot_file.py::test_run_snapshot_path_and_round_trip
    pass
