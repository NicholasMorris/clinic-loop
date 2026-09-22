# Triage Graph

`build_triage_graph()` (`src/clinicloop/agents/triage/graph/builder.py`) assembles the
triage agent's LangGraph `StateGraph`: a compliance-gated pipeline from an inbound
support message to either a sent reply, a human-review handoff, or an escalation --
with a real human-approval pause in the middle.

## Node walkthrough

The compiled graph's node set is exactly `EXPECTED_NODES`
(`src/clinicloop/agents/triage/graph/nodes.py`), 11 nodes:

```python
EXPECTED_NODES = frozenset(
    [
        "ingest",
        "classify_intent",
        "escalation_check",
        "resolve",
        "draft",
        "regulatory_guard",
        "human_approval",
        "guard_final",
        "send",
        "human_review",
        "escalate",
    ]
)
```

| Node | Purpose |
|---|---|
| `ingest` | Fetches the raw message body out-of-band via `MessageSource.fetch(message_id)`; only the opaque `message_id` ever passes through graph state or checkpoint config (see [triage-agent-port.md](triage-agent-port.md)'s privacy note). |
| `classify_intent` | Calls the model to classify the patient's message into one of the ten `Intent` values. |
| `escalation_check` | Runs the real escalation detector (`clinicloop.compliance.escalation.detector.detect`) against the message; sets `escalation_category`. |
| `resolve` | Calls tools (order status, order list) if the intent needs them, with a timeout. |
| `draft` | Calls the model to draft a reply; detects non-English input. |
| `regulatory_guard` | Runs the pre-send guard (`clinicloop.compliance.guard.core.check`) against the draft, before any human sees it. |
| `human_approval` | Pure pass-through node; the actual pause happens at compile time via `interrupt_before`. |
| `guard_final` | Re-runs the guard against the (possibly edited) text after human approval -- see "guard_final placement" below. |
| `send` | Calls `OutboundPort.send()` with the final text and the final `GuardVerdict`. This is the ONLY place a message is ever sent. |
| `human_review` | Terminal pass-through node for any case that needs a human to handle it directly. |
| `escalate` | Terminal pass-through node for a case the detector flagged for escalation. |

## The nine happy-path edges

Verified by `tests/agents/triage_graph/test_graph_shape.py`:

1. `ingest -> classify_intent`
2. `classify_intent -> escalation_check`
3. `escalation_check -> resolve` (conditional: `continue`, no escalation)
4. `resolve -> draft` (conditional: `ok`)
5. `draft -> regulatory_guard` (conditional: `ok`)
6. `regulatory_guard -> human_approval` (conditional: `ok`)
7. `human_approval -> guard_final` (conditional: `approve` or `edit`)
8. `guard_final -> send` (conditional: `ok`)
9. `escalation_check -> escalate` (conditional: `escalate`)

Plus the non-happy-path conditional edges each guarded node can also take:

| From | Condition | To |
|---|---|---|
| `resolve` | `state["routing_reason"] == "tool_timeout"` | `escalate` |
| `draft` | `state["routing_reason"] == "language"` | `human_review` |
| `regulatory_guard` | `state["routing_reason"] == "rule_block"` | `human_review` |
| `human_approval` | `human_decision.action == "reject"` | `human_review` |
| `guard_final` | `state["routing_reason"] == "rule_block"` | `human_review` |

## Terminal nodes and their reason codes

Three finish points (`graph.set_finish_point(...)`): `send`, `human_review`, `escalate`.
A case that reaches `send` has `escalation_category` in `(None, "none")` and a non-`None`
`draft`. A case that reaches `human_review` carries a `routing_reason` explaining why:

- `"tool_timeout"` -- a tool call in `resolve` exceeded its timeout
- `"language"` -- `draft` detected non-English input
- `"rule_block"` -- the guard (`regulatory_guard` or `guard_final`) rejected the draft
- no `routing_reason` at all -- the human explicitly rejected the draft at `human_approval`

A case that reaches `escalate` has a non-`"none"` `escalation_category` (one of
`adverse_event`, `pregnancy`, `distress`, `suspected_misuse`, `clinical_advice`, set by
the real `clinicloop.compliance.escalation.detector.detect()`).

## The human-gate contract

The graph is compiled with `interrupt_before=["human_approval"]`: execution genuinely
pauses there and the state is checkpointed. Resuming requires injecting a `HumanDecision`
via `update_state()` before calling `invoke(None, config)`:

```python
compiled.update_state(
    config,
    {
        "human_decision": HumanDecision(
            action="approve",  # or "edit" (with edited_text) or "reject"
            decided_by=...,
            decided_at=...,
        )
    },
)
compiled.invoke(None, config)
```

`route_human_decision` (the conditional-edge function on `human_approval`) reads
`state["human_decision"]` and **raises `ValueError`** if it is `None` -- a bare resume
with no injected decision fails loudly rather than silently defaulting to `"approve"`.
`action` determines the route: `"approve"` and `"edit"` both go to `guard_final`;
`"reject"` goes straight to `human_review`. If `action == "edit"`, the `send` node
uses `human_decision.edited_text` instead of the original `draft`.

`TriageAgentPort.serve()` (M2-7) auto-injects an `"approve"` decision for the simulation,
since a synchronous `serve()` call has no live human in the loop -- see
[triage-agent-port.md](triage-agent-port.md)'s "Simulation-only Auto-Approval" section.
The real product would instead leave the graph paused until M1-9's review console
supplies a real `HumanDecision`.

## The checkpoint thread-id rule

Every `invoke`/`update_state` call passes `config = {"configurable": {"thread_id":
case_id, "message_id": case_id}}`. `thread_id` is what LangGraph's `SqliteSaver` keys
checkpoints by, so **one case gets exactly one thread**: resuming a paused case means
calling `update_state`/`invoke(None, ...)` with the *same* `thread_id` it was invoked
with, never a fresh one. Reusing `case_id` for both `thread_id` and `message_id` keeps
the two concerns (checkpoint identity, and the opaque handle `ingest` fetches the raw
message by) trivially in sync without a second lookup table.

Every pydantic model or dataclass that can appear in `GraphState` must be listed in
`TRIAGE_ALLOWED_MSGPACK_MODULES` (`builder.py`) or it silently deserializes as a plain
dict after a real resume, breaking any node or router that expects the real type --
this broke `HumanDecision`-based routing during M2-5b's development before it was added.

## `guard_final` placement

The draft is checked against the guard **twice**: once by `regulatory_guard`, before
`human_approval` ever pauses (so a human never reviews a draft that would be rejected
anyway), and once by `guard_final`, after resuming, before `send`. The second check
exists because `action == "edit"` lets a human replace the draft text entirely --
`guard_final` is what re-validates *that* text before anything is actually sent. An
unedited, approved draft is checked again too (defense in depth: the state that
reaches `guard_final` is trusted less than the state `regulatory_guard` already
validated, since it passed through an external checkpoint/resume boundary in between).
