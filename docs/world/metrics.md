# Metrics: Throughput, Wait, SLA Breaches, and Cost

A `MetricSnapshot` is a frozen, versioned record of metrics for a completed simulation run. The same input always produces the same snapshot, enabling reproducible before-and-after comparisons.

## Metric Families

### Throughput

**Definition:**
- `orders_completed`: Number of orders that reached and finished the `pharmacy_fulfilment` queue.
- `orders_per_simulated_hour`: Throughput as orders per hour of simulated time.

**Computation:**
```
orders_completed = count(records where queue == "pharmacy_fulfilment" and finished_at is not None)
orders_per_simulated_hour = orders_completed / (duration_minutes / 60.0)
```

### Median Wait Per Queue

**Definition:**
- Per-queue median wait time, in simulated minutes, from enqueue to service start.
- Computed *per queue*, with no combined across-queue figure.
- For unstarted items, wait is measured from enqueue to end of run (duration).

**Wait time computation:**
```
For each item in a queue:
  if started_at is not None:
    wait = started_at - enqueued_at
  else:
    wait = duration_minutes - enqueued_at

median_wait_minutes[queue] = median(all waits in that queue)
```

Queues with no items have `median_wait_minutes[queue] = None`.

### SLA Breaches

**Definition:**
- A breach occurs when an item's wait time (time until service starts) exceeds its queue's target.
- Breaches are keyed by rule ID (not queue name), and each entry includes:
  - `rule_id`: The ID of the SLA rule (e.g., "termination_cutoff", "dispatch_commitment")
  - `count`: The number of breaches for this rule
  - `inventory_id`: The ID cited by this rule, from `sla_rules()`

**SLA Targets (from `src/clinicloop/world/config/sla_targets.toml`):**
- `intake`: 60 minutes
- `prescriber_review`: 240 minutes
- `pharmacy_fulfilment`: 480 minutes
- `support_inbox`: 120 minutes

All targets are assumed values and must be measured or validated before deployment.

**Computation:**
```
For each item in each queue:
  if wait > target_minutes[queue]:
    count breach for the rule associated with this queue

Breach entry = {
  rule_id: rule ID from sla_rules(),
  count: number of breaches,
  inventory_id: from sla_rules()[rule_id]
}
```

### Cost Per Order

**Definition:**
- Cost per order = (total staffing cost for busy time) / (completed orders)
- Staffing cost includes only busy time (time workers are actually serving items), not idle capacity.
- Returns `None` if zero orders completed to avoid division by zero.

**Rationale for excluding idle capacity:**
- Idle staffed capacity (workers standing by with no items to serve) is a scheduling decision, not a service cost.
- Cost per order measures the direct labor cost of completing orders, independent of staffing levels.
- Idle capacity is already visible in the dashboard metrics (staffing level, wait times).

**Computation:**
```
For each queue:
  busy_minutes = sum(finished_at - started_at for all items with both started_at and finished_at)
  busy_hours = busy_minutes / 60.0
  queue_cost = busy_hours * hourly_cost[queue]

total_cost = sum(queue_cost for all queues)
cost_per_order = total_cost / orders_completed (or None if orders_completed == 0)
```

## MetricSnapshot Schema

A `MetricSnapshot` is a Pydantic model with these fields:

```python
class MetricSnapshot(BaseModel):
    schema_version: str  # Always "1" (for forward compatibility)
    throughput: ThroughputMetrics  # orders_completed, orders_per_simulated_hour
    median_wait_minutes: dict[str, float | None]  # Keyed by queue name
    sla_breaches: dict[str, SLABreach]  # Keyed by rule_id
    cost_per_order: float | None  # None if zero orders
```

The model is **frozen** (immutable); assignment to any field raises `ValidationError`.

## File Storage

Run snapshots are stored as JSON files in `var/snapshots/run-<seed>.json`, where `<seed>` is the random seed used to generate the world.

**JSON format:**
```json
{
  "schema_version": "1",
  "seed": 20260921,
  "throughput": {
    "orders_completed": 123,
    "orders_per_simulated_hour": 2.5
  },
  "median_wait_minutes": {
    "intake": 15.5,
    "prescriber_review": 45.0,
    "pharmacy_fulfilment": null,
    "support_inbox": 30.0
  },
  "sla_breaches": {
    "termination_cutoff": {
      "rule_id": "termination_cutoff",
      "count": 5,
      "inventory_id": "ps-03"
    }
  },
  "cost_per_order": 42.5
}
```

**Path conventions:**
- Default directory: `var/snapshots/` (relative to repository root)
- File naming: `run-<seed>.json` (e.g., `run-20260921.json`)
- `read_run_snapshot(path)` and `write_run_snapshot(snapshot, seed)` handle I/O

## Empty Run Rule

A run with zero completed orders (no items finished pharmacy_fulfilment):
- `throughput.orders_completed = 0`
- `throughput.orders_per_simulated_hour = 0.0`
- `cost_per_order = None` (not `inf` or `NaN`)
- `median_wait_minutes` still computed for items that arrived but did not complete
- `sla_breaches` may still be non-empty (items can breach SLA without completing)

## Determinism

`compute_snapshot(run_result)` is a pure function of the `RunResult` event log. The same run always produces identical JSON when serialized. This ensures that before-and-after comparisons are meaningful and reproducible.
