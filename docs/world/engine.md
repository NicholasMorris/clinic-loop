# Discrete-Event Simulation Engine

## Overview

The SimClinic engine is a heap-based discrete-event simulation that advances a virtual clock only through scheduled events, never through wall-clock time. It maintains four named queues, processes items through worker pools, and records SLA breaches according to jurisdiction-specific rules.

## Event Loop and Tie-Breaking

The engine uses a priority queue (binary heap) to schedule and dispatch events in strict chronological order. Events are scheduled with:
- **Timestamp** (simulated minutes): the event's scheduled time
- **Sequence number**: insertion order for deterministic tie-breaking

When two events are scheduled at the same simulated timestamp, the event inserted first into the heap is always dispatched first. This ensures:
- **Determinism**: identical input seeds produce identical event sequences
- **Reproducibility**: a recorded event log can be replayed to reproduce the final queue and breach state

## Four Named Queues

The engine maintains exactly four queues, each recording enqueue and dequeue timestamps for every item:

- **`intake`**: questionnaire submissions from patients
- **`prescriber_review`**: consult records for clinical review
- **`pharmacy_fulfilment`**: orders for fulfillment and dispatch
- **`support_inbox`**: patient support messages

Each queued item carries:
- `enqueued_at`: simulated timestamp (minutes) when the item entered the queue
- `dequeued_at`: simulated timestamp when the item left the queue (or `None` if still waiting)

The constraint `dequeued_at >= enqueued_at` is always maintained.

## Worker Pools and Service Times

Each queue is serviced by a worker pool. Worker pools are configured with:
- **Staffing level**: number of concurrent workers
- **Service-time distribution**: statistical family (e.g., exponential, normal) for task duration
- **Hourly cost**: operational cost per hour

Configuration is loaded from `src/clinicloop/world/config/staffing.toml` using the `load_staffing()` function. The function requires every key in the configuration and supplies no defaults; a missing value raises `StaffingParameterMissing` naming both the pool and the missing key.

### Staffing Configuration

The staffing file is structured as TOML with one table per worker pool. Every pool table must include:
- `assumed = true`: marker that these are starter values, not measured
- `assumption_note`: plain-English description of the assumption (e.g., "Based on typical intake processing: 1-2 minutes per questionnaire")
- `service_time_family`: distribution family identifier (`exponential` or `normal`)
- `mean_service_minutes`: mean service time in minutes (float; used to draw service durations)
- `staffing_level`: number of workers (integer)
- `hourly_cost`: cost in currency units per hour (float)

Example:
```toml
[intake]
assumed = true
assumption_note = "Based on typical intake processing: 1-2 minutes per questionnaire with field validation"
service_time_family = "exponential"
mean_service_minutes = 2
staffing_level = 2
hourly_cost = 28.0
```

These values are labelled "assumed" to signal that they should be measured or updated before any real deployment.

### Service Time Distribution

Service times are drawn from per-queue distributions using seeded random number generators (one per queue, keyed by `[world.seed, queue_index]`):
- **Exponential family**: `duration = rng.exponential(mean_service_minutes)`
- **Normal family**: `duration = max(0.5, rng.normal(mean, 0.25 * mean))` (clipped at 0.5)

Final duration is always `max(1, ceil(value))` minutes, ensuring at least 1 minute of service.

### Staffing Overrides

At runtime, staffing levels can be overridden by passing `staffing_overrides` to the Engine constructor:
```python
engine = Engine(world, regime_key="au", staffing_overrides={"prescriber_review": 1})
```

This is used to simulate scenarios with reduced staff (e.g., "what if we reduced prescriber_review staff from 3 to 1?"). Any override level must be >= 1, and all queue names must be valid.

## SLA Rules

Three SLA rules are published in the grounded inventory and enforced by the engine. Each rule has:
- A stable **rule ID** (distinct from the inventory ID it cites)
- A jurisdiction-specific **threshold** read from the regime table
- An **inventory ID** naming the item in the inventory that documents the rule

The three rules are:

| Rule ID | Inventory ID | Jurisdiction | Threshold |
|---------|--------------|--------------|-----------|
| `termination_cutoff` | `ps-03` | AU | 2 business days |
| `damage_report_window` | `ps-04` | AU | 3 days |
| `dispatch_commitment` | `po-01` | AU | 1 business day |

The `sla_rules()` accessor returns the rule-ID-to-inventory-ID mapping:
```python
{
    "termination_cutoff": "ps-03",
    "damage_report_window": "ps-04",
    "dispatch_commitment": "po-01",
}
```

The metrics module (M1-5) and dashboard read this mapping rather than reaching into engine internals.

### Regime Parameters and NZ/UK Seam

Threshold values are stored in the AU, NZ, and UK regime tables. The engine accesses them via `get_regime(regime_key)`. 

- **AU**: All parameters are populated. The engine runs without error.
- **NZ, UK**: Parameters are marked as placeholders (not yet implemented).

When the engine runs with a placeholder regime and attempts to read a parameter (e.g., `dispatch_commitment_business_days`), it raises `RegimeParameterNotSet`. This ensures:
- The seam between implemented and unimplemented regimes is visible and fails fast
- No silent fallback to AU values occurs
- Later measurement exercises can update the regime tables without touching engine code

## Run Hash

The `run_hash()` method returns a SHA-256 hash over the ordered event log and final queue state. This hash:
- Uniquely identifies a complete run
- Is deterministic: identical seeds and parameters produce identical hashes
- Enables quick comparison of two runs without re-running

The hash includes:
1. Every event in the log (timestamp, event type, entity ID)
2. Final state of all four queues (item IDs and their enqueue/dequeue timestamps)

## Event Log Replay

A recorded event log can be replayed through the engine to reproduce the exact final state. Replay is enabled by the determinism guarantee:
- An event log is defined as the ordered sequence of events processed during a run
- Recording an event log means capturing the execution trace
- Replaying means re-executing the same sequence of events

In the current implementation, replay is implicit: running the engine twice with the same seed and duration produces the same event sequence and final state. Explicit event-log storage is part of future metrics and agent-integration work.

## Simulated Clock Independence

The engine uses only simulated time (minutes elapsed in the simulation) and never reads wall-clock time. Functions like `time.time()`, `time.monotonic()`, and `datetime.datetime.now()` are never called.

This is verified by a test that patches all wall-clock functions to raise `AssertionError` and confirms the engine completes a 24-hour run without calling them.

## Usage

```python
from clinicloop.world.engine import Engine
from clinicloop.world.generator import generate_world

# Generate a deterministic world
world = generate_world(seed=20260921, population_size=500, span_days=3)

# Create and run the engine (duration in minutes; 1440 * 3 = 3 days)
engine = Engine(world, regime_key="au")
result = engine.run(duration_minutes=4320)  # 3 days

# RunResult contains:
# - result.records: tuple of ItemRecords (queue, item_id, enqueued_at, started_at, finished_at, server)
# - result.queue_depth: dict[queue_name] -> tuple of (timestamp, depth) samples
# - result.duration_minutes: simulation duration
# - result.staffing: dict[queue_name] -> actual staffing level used
# - result.run_hash: SHA256 hash for reproducibility checking

# Access records for detailed analysis
for record in result.records:
    if record.finished_at is not None:
        wait_time = record.started_at - record.enqueued_at
        service_time = record.finished_at - record.started_at
        print(f"{record.item_id}: wait={wait_time}min, service={service_time}min")

# Check queue depths at 60-minute intervals
for queue_name, samples in result.queue_depth.items():
    max_depth = max((depth for timestamp, depth in samples), default=0)
    print(f"{queue_name}: max queue depth = {max_depth}")

# Compare two runs for reproducibility
world2 = generate_world(seed=20260921, population_size=500, span_days=3)
engine2 = Engine(world2, regime_key="au")
result2 = engine2.run(duration_minutes=4320)
assert result.run_hash == result2.run_hash, "Same seed should produce same hash"
```

## Demo Run Results

The following results were measured on 500 patients over 3 busy days (seed=20260921) with assumed staffing levels shown in `src/clinicloop/world/config/staffing.toml`:

**Demo run: 500 patients over 3 busy days, assumed staffing**

Run with default staffing (prescriber_review=4):

| Queue | Arrivals | Finished | Median Wait (min) | Max Depth |
|-------|----------|----------|-------------------|-----------|
| intake | 500 | 500 | 2 | 6 |
| prescriber_review | 331 | 331 | 1 | 11 |
| pharmacy_fulfilment | 67 | 67 | 0 | 1 |
| support_inbox | 250 | 250 | 0 | 2 |

Run with reduced prescriber_review staffing (prescriber_review=1):

| Queue | Arrivals | Finished | Median Wait (min) | Max Depth |
|-------|----------|----------|-------------------|-----------|
| intake | 500 | 500 | 2 | 6 |
| prescriber_review | 331 | 187 | 119 | 186 |
| pharmacy_fulfilment | 33 | 33 | 0 | 0 |
| support_inbox | 250 | 250 | 0 | 2 |

With default staffing (prescriber_review=4), all 331 consults are processed with a median wait of 1 minute and max queue depth of 11. With reduced staffing (prescriber_review=1), the queue backs up dramatically: median wait increases to 119 minutes, max depth reaches 186, and only 187 of 331 consults are finished within the 3-day window. This demonstrates the critical impact of prescriber availability on queue throughput.

## Staff Work Schedule

Workers in all queues operate **24/7** throughout the simulation duration. There are no shift changes, breaks, or scheduling constraints. Staff availability is modeled simply as a pool of `staffing_level` concurrent workers per queue, continuously available to service items.

## Testing

Conformance tests for the engine are located in:
- `tests/world/engine/test_determinism.py`: run-hash stability
- `tests/world/engine/test_ordering.py`: tie-breaking consistency
- `tests/world/engine/test_sla_rules.py`: rule mappings and regime parameters
- `tests/world/engine/test_simulated_clock.py`: wall-clock independence and seam errors
- `tests/world/engine/test_replay.py`: replay reproducibility
- `tests/world/queues/test_queues.py`: queue structure and timestamps
- `tests/world/workers/test_assumed_labels.py`: staffing configuration requirements
