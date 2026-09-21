#!/usr/bin/env python3
"""Compute and display metrics tables for SimClinic runs.

Generates metrics tables for the 500-patient 3-day world with default staffing
and with prescriber_review overridden to 1, demonstrating the impact of reducing
staffing on queue performance.
"""

from clinicloop.world.engine import Engine
from clinicloop.world.generator import generate_world
from clinicloop.world.metrics import compute_snapshot


def main() -> None:
    """Compute and display metrics for the test world."""
    print("=" * 80)
    print("SimClinic Metrics: 500-patient 3-day world")
    print("=" * 80)
    print()

    # Generate the world (500 patients, 3 days, deterministic seed)
    world = generate_world(seed=20260921, population_size=500, span_days=3)

    # Duration: 3 days = 3 * 24 * 60 = 4320 minutes
    duration = 4320

    # Run 1: Default staffing
    print("Configuration 1: Default staffing")
    print("-" * 80)
    engine_default = Engine(world, regime_key="au")
    result_default = engine_default.run(duration)
    snapshot_default = compute_snapshot(result_default)
    print_metrics(snapshot_default, "Default")
    print()

    # Run 2: prescriber_review override to 1
    print("Configuration 2: prescriber_review staffing = 1 (reduced from 4)")
    print("-" * 80)
    engine_override = Engine(world, regime_key="au", staffing_overrides={"prescriber_review": 1})
    result_override = engine_override.run(duration)
    snapshot_override = compute_snapshot(result_override)
    print_metrics(snapshot_override, "Override")
    print()

    # Side-by-side comparison
    print("=" * 80)
    print("SIDE-BY-SIDE COMPARISON")
    print("=" * 80)
    print()
    print(f"{'Metric':<40} {'Default':<20} {'Override (PR=1)':<20}")
    print("-" * 80)

    print(
        f"{'Orders completed':<40} {snapshot_default.throughput.orders_completed:<20} {snapshot_override.throughput.orders_completed:<20}"
    )
    print(
        f"{'Throughput (orders/hour)':<40} {snapshot_default.throughput.orders_per_simulated_hour:<20.2f} {snapshot_override.throughput.orders_per_simulated_hour:<20.2f}"
    )
    print()

    print("Median wait times (minutes):")
    for queue in ["intake", "prescriber_review", "pharmacy_fulfilment", "support_inbox"]:
        wait_default = snapshot_default.median_wait_minutes.get(queue)
        wait_override = snapshot_override.median_wait_minutes.get(queue)

        wait_default_str = f"{wait_default:.1f}" if wait_default is not None else "None"
        wait_override_str = f"{wait_override:.1f}" if wait_override is not None else "None"

        print(f"  {queue:<36} {wait_default_str:<20} {wait_override_str:<20}")

    print()
    print("Max queue depths:")
    for queue in ["intake", "prescriber_review", "pharmacy_fulfilment", "support_inbox"]:
        depths_default = result_default.queue_depth.get(queue, ())
        depths_override = result_override.queue_depth.get(queue, ())

        max_depth_default = max((d for _, d in depths_default), default=0) if depths_default else 0
        max_depth_override = (
            max((d for _, d in depths_override), default=0) if depths_override else 0
        )

        print(f"  {queue:<36} {max_depth_default:<20} {max_depth_override:<20}")

    print()
    print("SLA Breaches:")
    for rule_id in sorted(
        set(
            list(snapshot_default.sla_breaches.keys()) + list(snapshot_override.sla_breaches.keys())
        )
    ):
        breach_default = snapshot_default.sla_breaches.get(rule_id)
        breach_override = snapshot_override.sla_breaches.get(rule_id)

        count_default = breach_default.count if breach_default else 0
        count_override = breach_override.count if breach_override else 0

        print(f"  {rule_id:<36} {count_default:<20} {count_override:<20}")

    print()
    print(
        f"{'Cost per order':<40} {snapshot_default.cost_per_order:<20.2f} {snapshot_override.cost_per_order:<20.2f}"
    )
    print()

    # Assertions for test verification
    print("=" * 80)
    print("TEST ASSERTIONS")
    print("=" * 80)

    # Assert that prescriber_review override has more breaches
    pr_breaches_default = snapshot_default.sla_breaches.get("dispatch_commitment")
    pr_breaches_override = snapshot_override.sla_breaches.get("dispatch_commitment")

    count_default = pr_breaches_default.count if pr_breaches_default else 0
    count_override = pr_breaches_override.count if pr_breaches_override else 0

    assert count_override > count_default, (
        f"Override should have more prescriber_review breaches: {count_override} vs {count_default}"
    )
    print(f"✓ Override prescriber_review breaches ({count_override}) > default ({count_default})")

    # Assert determinism
    result_default_2 = engine_default.run(duration)
    snapshot_default_2 = compute_snapshot(result_default_2)
    assert snapshot_default.model_dump() == snapshot_default_2.model_dump(), (
        "Same engine configuration should produce identical metrics"
    )
    print("✓ Determinism verified: same input produces identical metrics")

    # Assert cost calculation
    assert snapshot_default.cost_per_order is not None, (
        "Default run should have non-zero cost per order"
    )
    assert snapshot_override.cost_per_order is not None, (
        "Override run should have non-zero cost per order"
    )
    print(
        f"✓ Cost per order computed: default={snapshot_default.cost_per_order:.2f}, override={snapshot_override.cost_per_order:.2f}"
    )

    print()
    print("=" * 80)
    print("All tests passed!")
    print("=" * 80)


def print_metrics(snapshot, label: str) -> None:
    """Print a formatted metrics snapshot."""
    print(f"Orders completed: {snapshot.throughput.orders_completed}")
    print(f"Throughput: {snapshot.throughput.orders_per_simulated_hour:.2f} orders/hour")
    print()

    print("Median wait times (minutes):")
    for queue, wait in sorted(snapshot.median_wait_minutes.items()):
        if wait is None:
            print(f"  {queue}: None (no items)")
        else:
            print(f"  {queue}: {wait:.1f}")
    print()

    print("SLA breaches:")
    if snapshot.sla_breaches:
        for rule_id, breach in sorted(snapshot.sla_breaches.items()):
            print(f"  {rule_id} ({breach.inventory_id}): {breach.count} breaches")
    else:
        print("  (none)")
    print()

    if snapshot.cost_per_order is None:
        print("Cost per order: None (zero orders completed)")
    else:
        print(f"Cost per order: {snapshot.cost_per_order:.2f}")


if __name__ == "__main__":
    main()
