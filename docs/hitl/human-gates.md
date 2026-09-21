# Human-in-the-Loop Kernel

The HITL kernel provides a shared infrastructure for all agent graphs to pause for human approval, collect human input, and preserve state across process restarts.

## Overview

Four agent graphs need human intervention at critical points:
- **Triage**: Draft message must be approved by a clinician before sending.
- **Integrity**: Review flags are prepared but a human decides the action.
- **Consult**: Extracted notes are drafted but require clinician sign-off.
- **Factory**: Implemented code is shown to the operator, who decides to deploy or iterate.

The HITL kernel provides:
1. **HumanDecision** model: Structured type for human decisions (approve, edit, reject).
2. **Checkpointing**: Durable storage of interrupted states per agent.
3. **Approval gates**: Static interrupts that block execution until a decision arrives.
4. **Question loops**: Dynamic interrupts for multi-turn conversation.
5. **Review console backend**: Query interrupted threads across agents.

## HumanDecision Model

```python
from clinicloop.hitl import HumanDecision
from datetime import datetime

decision = HumanDecision(
    action="approve",  # "approve" | "edit" | "reject"
    decided_by="clinician-001",  # WHO made the decision
    decided_at=datetime.now(),  # WHEN
    edited_text=None,  # Optional; required if action="edit"
)
```

### Validation Rules

- **action**: One of `"approve"`, `"edit"`, `"reject"`.
- **decided_by**: String identifier of the person making the decision.
- **decided_at**: ISO 8601 timestamp.
- **edited_text**: Must be provided (non-empty string) if `action == "edit"`. Raises `ValidationError` otherwise.

## Typed State Schema

Each reference graph and agent graph uses a **typed state schema** (TypedDict) so that all fields are statically known and runtime errors are caught early by mypy.

```python
from typing import TypedDict, NotRequired

class CaseState(TypedDict):
    """State for a triage case."""
    case_id: str  # Required
    next: NotRequired[tuple[str, ...]]  # Optional; set by LangGraph
    outcome: NotRequired[str]  # Optional; "approved", "rejected", or "edited"
    decided_by: NotRequired[str]  # Optional; who made the decision
```

This TypedDict is passed to `StateGraph(CaseState)` so the graph enforces the schema.

## Approval Gate Pattern

An **approval gate** is a node that pauses the graph and waits for a human decision. The graph is compiled with `interrupt_before=["human_approval"]` so that the node is never actually executed; instead, the graph halts and returns to the caller.

### Example

```python
from langgraph.graph import StateGraph
from clinicloop.hitl import HumanDecision

# Build graph with approval gate
graph = StateGraph(CaseState)

# ... add other nodes ...

graph.add_node("human_approval", lambda s: s)  # No-op; interrupt prevents execution
graph.add_conditional_edges(
    "human_approval",
    lambda s: "approve_path" if s.get("outcome") == "approved" else "reject_path",
    {"approve_path": "send", "reject_path": "reject"},
)

compiled = graph.compile(interrupt_before=["human_approval"])

# Run the graph
config = {"configurable": {"thread_id": "case-0001"}}
initial_state = {"case_id": "case-0001", "next": ()}

for event in compiled.stream(initial_state, config):
    pass  # Graph stops at human_approval node

# Inject decision
decision = HumanDecision(
    action="approve",
    decided_by="clinician-001",
    decided_at=datetime.now(),
)
compiled.update_state(
    config,
    {
        "outcome": "approved",
        "decided_by": decision.decided_by,
        "decided_at": str(decision.decided_at),
    },
)

# Resume
for event in compiled.stream(None, config, input=None):
    pass  # Continues from human_approval to "send"
```

### Why Static Interrupt?

The brief specifies `interrupt_before` (L3) because approval gates are **declarative and predictable**: the human always approves or rejects at the same point. LangGraph's documentation also recommends static interrupts for this pattern.

See `docs/adr/human-gates.md` for alternatives considered.

## Dynamic Interrupt Question Loop

For **multi-turn conversations** (e.g., Factory interviewing an operator), use dynamic `interrupt()` to ask questions one by one without pre-declaring all nodes.

```python
from langgraph.graph import StateGraph

graph = StateGraph(CaseState)

def interview_node(state: CaseState) -> dict:
    """Interview node that asks questions dynamically."""
    # In a real scenario, the LLM decides what to ask next
    # For now, simulate two questions
    questions = ["What is the process?", "What are the success criteria?"]
    answers = []
    
    for question in questions:
        # Pause for input
        graph.interrupt(value={"question": question})
        # Resume provides the answer
        # (In practice, the graph context provides the answer via update_state)
        answers.append("...")
    
    return {"answers": answers}
```

Dynamic interrupts are called from within node logic, allowing the node to decide whether and when to pause.

See `docs/adr/human-gates.md` for the design rationale.

## Checkpointing and Durability

Each agent uses its own SQLite database to checkpoint state. The database is located at `var/checkpoints/<agent_name>.sqlite`.

```python
from clinicloop.hitl import build_checkpointer

checkpointer = build_checkpointer("triage")
# Returns SqliteSaver backed by var/checkpoints/triage.sqlite

# Pass to the graph at compile time
graph = StateGraph(...).compile(
    checkpointer=checkpointer,
    interrupt_before=["human_approval"],
)
```

### Thread ID Convention

The **thread ID** is the **case ID** (e.g., `"case-0001"`). This ensures that each clinical case has its own execution thread and checkpoint.

```python
config = {
    "configurable": {
        "thread_id": "case-0001",  # Your case ID
        "checkpoint_saver": checkpointer,
    }
}
graph.stream(initial_state, config)
```

When the graph is interrupted or the process restarts, call `graph.get_state(config)` to resume from the last checkpoint.

### One Database Per Agent

Storing checkpoints in one database per agent (not one per run or monolithic) makes it easy to:
- Query all pending decisions for one agent.
- Back up or restore individual agents independently.
- Avoid bottlenecks on a single database file.

See `docs/adr/checkpointing.md` for alternatives.

## Review Console Backend

```python
from clinicloop.hitl import list_pending

# Get all pending approvals for Triage
pending_case_ids = list_pending("triage")
# Returns ["case-0001", "case-0003", ...] — cases currently interrupted at human_approval

for case_id in pending_case_ids:
    # Fetch the case details, show to clinician
    # When decision arrives, call graph.update_state(...) with the HumanDecision
    pass
```

The review console uses `list_pending()` to display all pending cases across agents and allows the clinician to navigate to each one and provide a decision.

## Testing

Tests use the fake model (M0-7a) so no real LLM is loaded. Each test:
1. Builds the reference graph.
2. Runs it until interrupted.
3. Verifies the graph stopped at the expected node.
4. Injects a decision via `update_state()`.
5. Resumes and verifies the outcome.

All tests are part of `make ci` and run without network access (pytest-socket enforces loopback only).

## Reference Implementation

The `clinicloop.hitl.reference_graph` module provides a complete example:
- Typed `ReferenceState` TypedDict.
- `build_reference_graph()` function that returns a compiled graph.
- Two conditional edges from the `human_approval` node.
- Acceptance tests in `tests/hitl/` that verify all seven acceptance criteria (AC1–AC7).
