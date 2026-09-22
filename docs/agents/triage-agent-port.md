# Triage Agent Port

The TriageAgentPort adapter integrates the triage LangGraph agent into the SimClinic engine as a replaceable worker for the support inbox queue.

## The AgentPort Protocol

The `AgentPort` protocol (defined in `clinicloop.world.ports.protocol`) specifies how agents replace human worker steps:

```python
class AgentPort(Protocol):
    def serve(self, case_id: str) -> float:
        """Serve a case, returning service time in minutes.
        
        Raises RuntimeError (or any exception): case falls back to human pool
        and a PortFailure record is written.
        """
        ...
```

The engine registers a TriageAgentPort under the `"triage"` scope in a PortRegistry. When an incoming support message arrives and the `triage` toggle is ON, the engine calls `port.serve(message_id)` instead of its default RNG-based shortcut. If `serve()` raises `RuntimeError`, the message is immediately routed to the human support inbox queue and the exception type is recorded.

## The WorldMessageSource Adapter

The TriageAgentPort stores a `WorldMessageSource` that implements the `MessageSource` protocol, allowing the triage graph to fetch raw message text by `message_id`:

```python
class WorldMessageSource:
    def __init__(self, world: World) -> None:
        self.world = world

    def fetch(self, message_id: str) -> str:
        # Looks up message in world.messages by message_id
        # Returns the message body text
        # Raises KeyError if not found
```

This decouples the graph from the world model and ensures only the opaque message ID travels through the checkpoint database (avoiding PII leakage).

## Simulation-only Auto-Approval

In the real SimClinic product, human approval gates (`interrupt_before=['human_approval']`) block execution until a clinician reviews the draft and supplies a `HumanDecision` (approve, edit, or reject).

In this simulation, **TriageAgentPort automatically approves every draft that reaches the human_approval gate**, using `update_state()` to inject a pre-approved `HumanDecision(action='approve', decided_by='triage-agent-port')` and resume the graph.

**This is a demo simplification only.** The real product never auto-approves agent drafts. Real deployments would require M2-5b's interrupt/checkpoint mechanism and M1-9's review console to handle clinician decisions. This adapter's auto-approval exists solely to measure the agent's throughput effect on queue depth in the synthetic simulation.

The auto-approval only ever applies to the ORIGINAL, unedited draft (no `edited_text`). If a clinician edits the text in the real product, the adapter would never see that edited decision; only the original draft can be auto-approved here.

## Exception Types and Fallback Routing

The TriageAgentPort raises three custom exceptions (all subclasses of `RuntimeError`) to signal different outcomes:

### `CaseEscalated(case_id)`

Raised when the triage graph ends at the `escalate` terminal (e.g., adverse event, severe distress, or other clinical escalation conditions). The engine catches this, records a `PortFailure(scope='triage', exception_type='CaseEscalated', case_id=...)`, and routes the case to the human support queue.

### `DraftNeedsHumanReview(case_id, routing_reason)`

Raised when the graph ends at the `human_review` terminal due to:
- `routing_reason='language'`: non-English message detected
- `routing_reason='rule_block'`: draft text blocked by regulatory guard rules

The engine records a `PortFailure` with `exception_type='DraftNeedsHumanReview'` and routes the case to the human queue for manual handling.

### `HumanApprovalPending(case_id)`

Raised (rarely) if `update_state()` or the post-approval `invoke()` raises an exception during the auto-approval resume (e.g., a genuine `ValueError` from `guard_final`). This signals a real error in the agent itself, not a normal routing decision.

All three exceptions are subclasses of `RuntimeError`, so the engine's fallback-to-human contract is satisfied: any exception means the case is handed to the human pool, and a PortFailure record is written.

## Service Time and Agent Configuration

The TriageAgentPort reads the assumed agent service time from the SimClinic configuration:

```python
from clinicloop.world.workers import load_agents
agent_config = load_agents()
simulated_minutes = agent_config.triage.agent_service_minutes  # Read-only
```

This value is assumed and measured separately in M0-7a. It represents the time the simulation allocates for an agent-resolved case. It is not defined or tuned by this issue; it is merely READ from the existing configuration.

When `serve()` completes successfully (outcome='sent'), it returns `float(simulated_minutes)`, which the engine uses to schedule a finish event for the item.

## Available Capacity and Per-Tick Observation

The Engine exposes a per-tick callback (`on_tick: Callable[[int, dict[str, int]], None]`) invoked every 60 simulated minutes with:

```python
on_tick(timestamp, available_capacity)
# available_capacity[queue] = staffing[queue] - busy[queue]
```

This callback is observational only: it does not change engine behavior and does not control the toggle. The test uses `on_tick` to record the human worker pool's available capacity over time.

**Capacity itself is toggle-invariant.** The staffing level (`staffing[queue]`) is fixed. The busy count (`busy[queue]`) is determined by which items are currently being served by human workers. Agent-resolved items never occupy a human server slot, so they do not appear in the busy count. As a result:

- When the toggle is ON, the agent resolves some items immediately, leaving more human server capacity free
- When the toggle is OFF, those same items would occupy human servers, reducing free capacity
- However, **staffing and capacity are properties of the human worker pool itself**, not of the agent

The triage agent merely shifts DEMAND onto the support inbox queue (reducing it when on, raising it when off), but does not change the staffing level or the maximum capacity.

## Determinism

The TriageAgentPort is deterministic given:
1. The same world (seeded)
2. The same model (FakeModelPort with scripted responses, or CassetteModelPort)
3. A fresh in-memory `SqliteSaver` per case

The compiled graph receives the same input state and model outputs, so it produces the same output state every time. This is sufficient to make engine runs deterministic (per AC3).

## Proof of Concept

See `tests/agents/triage_port/` for six test modules covering:

- **test_protocol.py** (AC1): Runtime `isinstance` check and basic serve() execution
- **test_toggle_effect.py** (AC2): Support inbox depth and wait rise when agent is off
- **test_determinism.py** (AC3): Identical run hashes for same seed and toggle state
- **test_human_gate_handoff.py** (AC4): Port failures correctly fall back to human queue
- **test_no_direct_send.py** (AC5): All text sends originate from the graph's send node via OutboundPort
- **test_capacity_restore.py** (AC6): Available capacity is observed correctly for both toggle states

See `tests/conformance/test_M2_7.py` for checklist conformance tests (C0, C1, X3).
