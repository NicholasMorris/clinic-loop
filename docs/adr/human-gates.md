# ADR: Static Interrupt Before vs Dynamic Interrupt for Human Gates

## Status

Accepted

## Context

Four agent graphs (Triage, Integrity, Consult, Factory) need mechanisms to pause for human approval before sending messages or proceeding with actions. The brief specifies `interrupt_before` for approval gates (L3). LangGraph provides two interrupt patterns: static `interrupt_before` and dynamic `interrupt()`. Each has different trade-offs in terms of coupling, testability, and multi-turn conversations.

## Decision

- **Approval gates** (Triage send, Consult signoff) use **static `interrupt_before`** with state updated via `update_state()` carrying a `HumanDecision`. This matches the brief's L3 requirement and keeps the gate logic simple and decoupled from the graph.
- **Multi-turn question and answer** (Factory interview) uses **dynamic `interrupt()`** because it is inherently multi-turn and stateless between resumptions. Dynamic interrupts avoid the need to pre-declare question nodes and allow the LLM to decide the next question.

## Consequences

**Static interrupt_before:**
- Interrupt points are declared at graph compile time, making them explicit and discoverable.
- State must be prepared by the caller before resumption; no mid-logic decision about whether to interrupt.
- Easier to test: the interrupt is guaranteed, no branching based on LLM output.
- Less flexible for dynamic flows (e.g., "ask a follow-up question if the answer is ambiguous").

**Dynamic interrupt():**
- Interrupts can be called from within node logic based on runtime conditions.
- Allows multi-turn flows without pre-declaring all question nodes.
- Harder to test: the test must simulate all the LLM's decisions to reach an interrupt.
- Couples interrupt logic to the node implementation.

## Alternatives considered

1. **Always use static `interrupt_before`**: Would require the Factory to pre-declare all possible question nodes, which is not feasible because the LLM may ask follow-up questions not known at compile time.

2. **Always use dynamic `interrupt()`**: Would make approval gates harder to test and reason about; the gate logic would be entangled with state management in the node.

3. **Use channels and reducers**: LangGraph's channel-based approach could model human input as a channel, but this requires more scaffolding and is less idiomatic than interrupts.

The chosen split gives each pattern its optimal use case: static for predictable, declarative gates; dynamic for emergent, multi-turn conversations.
