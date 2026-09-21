# Agent Port Protocol

The AgentPort protocol defines how an agent integrates with the SimClinic event engine, replacing one human worker step without changing the overall queue semantics.

## The Protocol

An `AgentPort` defines a single method:

```python
def serve(self, case_id: str) -> float:
    """Serve a case with the agent.
    
    Args:
        case_id: Unique case identifier.
    
    Returns:
        Service time in minutes (must be >= 0).
    
    Raises:
        RuntimeError: If the agent cannot serve; fallback to human pool.
    """
```

When a case reaches an agent's queue, the engine calls `serve()`. The agent processes the case and returns the service time in minutes. If `serve()` raises any exception, the case immediately falls back to the human worker pool, a `PortFailure` record is written, and the run continues—no case is lost.

## Toggleable Scopes

Exactly three scopes are toggleable:

- **`triage`**: Replaces the human support inbox pool. Processes inbound patient messages, resolves safe cases, and escalates others.
- **`integrity`**: Replaces the human integrity review step. Flags applications for clinical review based on behavioural signals.
- **`consult_documentation`**: Replaces the human consult note writer. Reviews drafted notes and codes clinical terms.

The Factory is **not toggleable**. Instead of toggling it on and off, the Factory reports measured impact by running the same process with and without the automation and comparing metrics. This allows quantifying the real benefit and cost of automation.

## FakeAgentPort: The Shipped Test Double

`FakeAgentPort` ships in `src/clinicloop/world/ports/fakes.py` (not the test tree) because the dashboard (M1-7) registers it for demo purposes. Real agent adapters (M2-7, M3-3, M5-8) replace it later without changing the seam.

A `FakeAgentPort` with `service_time_fraction=0.1` serves cases in one-tenth the time of the human pool's mean. When enabled, it reduces queue depth and median wait. When disabled (toggle off), the step returns to the human pool, making queue metrics visibly worsen. This demonstrates the toggle effect.

```python
from clinicloop.world.ports.fakes import FakeAgentPort

# Create a fake agent that serves in 10% of human mean time
port = FakeAgentPort(service_time_fraction=0.1)
service_time = port.serve("case_123")  # Returns ~0.1 minutes for demo
```

## Toggle Scheduling and Determinism

A toggle applies to cases **starting** after the toggle event, never mid-case. If a case is already in service when the toggle fires, it completes on the side it started (agent or human pool).

Toggle changes take effect at scheduled events, preserving run determinism. Two runs with identical toggle schedules and the same seed produce equal run hashes. Moving a toggle to a different simulated time changes the hash.

## Capacity Restoration

When a port is disabled, its worker capacity is released. The pool's staffed capacity with the port disabled equals the baseline no-agent capacity for that step. This ensures that toggling off a port restores full human capacity, making queues back up predictably.

## Port Failure Fallback

A `PortFailure` record is written when a port's `serve()` method raises an exception:

```python
@dataclass
class PortFailure:
    """Record of a port failure (exception during serve)."""
    scope: str  # "triage", "integrity", or "consult_documentation"
    exception_type: str  # Name of the exception class
    case_id: str  # The case that triggered the failure
```

The exception does not propagate; the case is immediately served by the human worker pool instead. This contract ensures that a misbehaving agent cannot silently drop cases—they fall back gracefully.

## Integration Example

The engine accepts an `agent_toggles` parameter mapping scope names to booleans:

```python
from clinicloop.world.engine import Engine
from clinicloop.world.ports import PortRegistry
from clinicloop.world.ports.fakes import FakeAgentPort

# Create a registry and register a fake triage agent
registry = PortRegistry()
registry.register("triage", FakeAgentPort(service_time_fraction=0.1))

# Run with the agent enabled
engine = Engine(world, regime_key="au", agent_toggles={"triage": True})
result_with_agent = engine.run(duration)

# Run with the agent disabled (same world, same seed)
engine = Engine(world, regime_key="au", agent_toggles={"triage": False})
result_without_agent = engine.run(duration)

# Compare metrics to measure toggle effect
from clinicloop.world.metrics import compute_snapshot
snapshot_with = compute_snapshot(result_with_agent)
snapshot_without = compute_snapshot(result_without_agent)

# With agent: lower support_inbox queue depth and median wait
assert snapshot_with.median_wait_minutes["support_inbox"] < \
       snapshot_without.median_wait_minutes["support_inbox"]
```

## Why Ship FakeAgentPort in src?

Real agent adapters need the same seam (AgentPort protocol) but are implemented as LangGraph graphs that call actual LLMs or decision logic. By shipping a deterministic fake in src/, the dashboard can register it for demos without importing test code. Later issues (M2-7, M3-3, M5-8) replace it with real adapters without changing how it's registered or toggled.

## Future Work

- **M2-7**: Triage agent adapter (LangGraph + real LLM)
- **M3-3**: Integrity agent adapter (signal detection + classification)
- **M5-8**: Consult documentation agent adapter (note review + coding)
- **M1-7**: Dashboard toggle widgets and FakeAgentPort registration
- **M6-5**: Factory impact measurement (automated vs manual baseline)
