#!/usr/bin/env python
"""Demo script: run the engine with default and reduced staffing, print metrics."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clinicloop.world.engine import Engine
from clinicloop.world.generator import generate_world


def calculate_metrics(result, queue_names):
    """Calculate and return metrics for a run."""
    metrics = {}

    for queue_name in queue_names:
        records = [r for r in result.records if r.queue == queue_name]

        # Count arrivals
        arrivals = len(records)

        # Count finished
        finished = sum(1 for r in records if r.finished_at is not None)

        # Calculate median wait time
        wait_times = [r.started_at - r.enqueued_at for r in records if r.started_at is not None]
        median_wait = sorted(wait_times)[len(wait_times) // 2] if wait_times else 0

        # Get max queue depth
        max_depth = (
            max((depth for ts, depth in result.queue_depth[queue_name]), default=0)
            if result.queue_depth[queue_name]
            else 0
        )

        metrics[queue_name] = {
            "arrivals": arrivals,
            "finished": finished,
            "median_wait_minutes": median_wait,
            "max_depth": max_depth,
        }

    return metrics


def main() -> None:
    """Run the demo."""
    queue_names = ["intake", "prescriber_review", "pharmacy_fulfilment", "support_inbox"]

    print("=" * 80)
    print("SimClinic Engine Demo Run")
    print("=" * 80)
    print()

    # Generate world: 500 patients over 3 busy days
    print("Generating world: 500 patients, 3 days...")
    world = generate_world(seed=20260921, population_size=500, span_days=3)
    print(f"  Questionnaires: {len(world.questionnaires)}")
    print(f"  Consults: {len(world.consults)}")
    print(f"  Orders: {len(world.orders)}")
    print(f"  Messages: {len(world.messages)}")
    print()

    # Run with default staffing
    staffing_default = (
        "Default: intake=1, prescriber_review=4, pharmacy_fulfilment=1, support_inbox=1"
    )
    print(f"Run 1: {staffing_default}")
    engine1 = Engine(world, regime_key="au")
    result1 = engine1.run(4320)  # 3 days in minutes
    metrics1 = calculate_metrics(result1, queue_names)
    print(f"  Hash: {result1.run_hash[:16]}...")
    print()

    # Run with reduced prescriber_review staffing
    print("Run 2: Reduced staffing (prescriber_review=1)")
    engine2 = Engine(world, regime_key="au", staffing_overrides={"prescriber_review": 1})
    result2 = engine2.run(4320)
    metrics2 = calculate_metrics(result2, queue_names)
    print(f"  Hash: {result2.run_hash[:16]}...")
    print()

    # Print comparison table
    print("=" * 80)
    print("Queue Metrics Comparison")
    print("=" * 80)
    print()
    print(f"{'Queue':<20} {'Arrivals':<10} {'Finished':<10} {'Median Wait':<15} {'Max Depth':<10}")
    print("-" * 80)

    for queue_name in queue_names:
        m1 = metrics1[queue_name]
        print(
            f"{queue_name:<20} {m1['arrivals']:<10} {m1['finished']:<10} "
            f"{m1['median_wait_minutes']:<15} {m1['max_depth']:<10}"
        )

    print()
    print("Run 2 (Reduced prescriber_review staff):")
    print()
    print(f"{'Queue':<20} {'Arrivals':<10} {'Finished':<10} {'Median Wait':<15} {'Max Depth':<10}")
    print("-" * 80)

    for queue_name in queue_names:
        m2 = metrics2[queue_name]
        print(
            f"{queue_name:<20} {m2['arrivals']:<10} {m2['finished']:<10} "
            f"{m2['median_wait_minutes']:<15} {m2['max_depth']:<10}"
        )

    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()
    print(
        f"Hashes are different: {result1.run_hash != result2.run_hash} "
        "(due to different staffing levels)"
    )
    print(
        f"Prescriber Review Max Depth Increase: "
        f"{metrics2['prescriber_review']['max_depth']} "
        f"(was {metrics1['prescriber_review']['max_depth']})"
    )
    print()


if __name__ == "__main__":
    main()
