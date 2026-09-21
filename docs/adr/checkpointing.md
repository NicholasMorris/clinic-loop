# ADR: SQLite Checkpointing with One Database Per Agent

## Status

Accepted

## Context

LangGraph agents need to persist their execution state so that interrupts survive process restarts. The demo must be reliable: if a clinician approves a case, the approval persists even if the process crashes and restarts. Without checkpointing, in-flight cases are lost and the review console cannot show pending decisions across restart boundaries.

LangGraph provides `SqliteSaver` for checkpointing. The decision concerns:
1. Database file organization: one monolithic database, one per agent, or one per run?
2. Thread ID convention: what identifies a unique case execution?

## Decision

- **One SQLite database per agent** at `var/checkpoints/<agent_name>.sqlite`.
- **Thread ID = case ID**: The case identifier (e.g., `case-0001`) is used as the `thread_id` when calling `graph.invoke(..., config={"configurable": {"thread_id": "case-0001"}})`.

This makes it easy for the review console to query a specific agent's pending threads, and the case ID is already the natural identifier for a clinical workflow.

## Consequences

**Advantages:**
- Simple schema: one table per agent, indexed by thread_id (case_id).
- Easy to query: "Get all pending approvals for the Triage agent" is a single database query.
- Easy to back up: each agent's database is independent; losing one agent's checkpoints does not lose others.
- Scales to many agents without a monolithic database.

**Disadvantages:**
- No cross-agent queries without joining multiple databases (minor; not needed for current design).
- Database files accumulate in `var/` across restarts; no automatic cleanup (noted as out of scope; retention policy deferred to later).

## Alternatives considered

1. **One monolithic checkpoint database**: Simpler schema but hard to isolate agents; all checkpoints in one file means a single-agent backup/restore affects the whole system.

2. **One database per run** (per invocation of the demo): Would require scanning all databases to find pending threads; the review console would not know which database to query without additional metadata.

3. **In-memory checkpointing**: Fast but loses state on restart; unacceptable for the reliability goal.

4. **Custom file-based checkpointing**: Would require implementing `BaseCheckpointSaver` ourselves; simpler to use LangGraph's built-in `SqliteSaver`.

The chosen design aligns with LangGraph's idiomatic use of checkpointing and makes the review console's job straightforward.
