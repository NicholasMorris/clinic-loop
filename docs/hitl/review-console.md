# Review Console

The review console provides a web interface for discovering pending human decisions and applying approvals, edits, or rejections to interrupted workflow items.

## Overview

When a LangGraph agent pauses at a human gate (using `interrupt_before`), the checkpoint database records the interruption. The review console discovers these pending items across all configured agent databases and presents them to a human reviewer for decision.

## Checkpoint Root Discovery

All agent checkpoint databases live under a single configured root directory, specified by the `CLINICLOOP_CHECKPOINT_ROOT` environment variable. If unset, it defaults to `var/checkpoints`.

The console discovers agent databases by finding all `*.sqlite` files directly under this root. Databases outside the root are never discovered, ensuring scope isolation. When querying an agent, the console:

1. Opens the agent's SQLite checkpoint database
2. Queries all distinct thread IDs (case IDs)
3. For each thread, retrieves the checkpoint state using the graph's accessor
4. Checks if the state's `.next` tuple is non-empty (indicating an active interruption)
5. Checks if `"human_decision"` is absent from the state values (indicating no prior decision)
6. If both conditions hold, the item is pending

The M0-7b kernel's list_pending was rewritten here because the first version could never find a thread: it hardcoded a cwd-relative path and queried a non-existent `next` column.

## Decision Kinds

The console accepts three decision kinds:

### Approve

Records a human approval and clears the pending state. The recorded decision carries:

- **kind**: "approve"
- **actor**: The reviewer ID (asserted locally; not authenticated)
- **decided_at**: ISO-8601 timestamp of the decision

Example:

```python
apply_decision(agent="triage", case_id="case_001", kind="approve", reviewer="dr_alice")
```

### Edit

Records an edited payload for the workflow to re-check. The console stores the edited text byte-for-byte as supplied, preserving unicode, whitespace, and trailing newlines. The decision carries:

- **kind**: "edit"
- **edited_text**: The edited payload bytes
- **actor**: The reviewer ID
- **decided_at**: ISO-8601 timestamp

The graph's guard_final node (inside each agent's workflow) is responsible for re-validating the edited text before proceeding, since the console has no knowledge of the agent's rules.

Example:

```python
apply_decision(
    agent="triage",
    case_id="case_001",
    kind="edit",
    reviewer="dr_bob",
    edited_text="Modified response text\n",
)
```

### Reject

Records a rejection with an optional reason. The decision carries:

- **kind**: "reject"
- **reason**: Optional reason for rejection
- **actor**: The reviewer ID
- **decided_at**: ISO-8601 timestamp

Example:

```python
apply_decision(
    agent="triage",
    case_id="case_001",
    kind="reject",
    reviewer="dr_charlie",
    reason="Requires clinician review",
)
```

## Recording Decisions

Decisions are recorded via `graph.update_state()`, writing only to the `"human_decision"` channel. This single-channel constraint ensures the console cannot accidentally overwrite other workflow state. The recorded dict validates against `clinicloop.hitl.decision.HumanDecision` when the kind is mapped to an action.

Once a decision is recorded, the item no longer appears in the pending list (because `"human_decision"` is now in the state values). Attempting to apply a second decision raises `DecisionAlreadyRecorded` and leaves the first decision unchanged.

The actor is supplied by the local operator and is not authenticated; the README states this limitation.

## Boundary Constraints

The console operates under strict isolation boundaries:

- **No signing.** The console imports neither `SignoffService` nor `SignedNote`. Sign-off happens only in the pipeline's `clinician_signoff` node via `SignoffService.sign()`, which the console cannot call.
- **No dashboard import.** The console does not import or touch the dashboard package, which is owned by M1-7.
- **Single-channel state writes.** Every `update_state` call passes only the `"human_decision"` key, enforced by a symbol-name scan.

These boundaries are verified by a scanning test that:

1. Parses every Python file in `hitl/console/` as an AST
2. Checks for imports of `clinicloop.dashboard` and `SignoffService` / `SignedNote`
3. Verifies all `update_state` calls pass a dict literal with only the `"human_decision"` key
4. Reports violations as AST nodes (class definitions, imports, attribute access)

The scan is proved by a decoy module `tests/hitl/console/decoy_signer.py` that defines a class `SignoffService`; running the scan against it confirms violations are detected.

## Testing

Console tests use `pytest-socket` configured to block non-loopback sockets, ensuring no network calls occur. All tests:

- Create a temporary checkpoint root under `pytest` tmp_path
- Monkeypatch `CLINICLOOP_CHECKPOINT_ROOT` to isolate from system state
- Build real reference graphs with SqliteSaver checkpointers
- Invoke graphs and query state directly; no mocks

## Streamlit Page

The console provides a Streamlit page at `clinicloop.hitl.console.page` that:

1. Lists all pending items in a dataframe (agent, case ID, interrupted node, timestamp)
2. Displays any errors reading agent databases
3. Allows selecting an item to review its payload
4. Provides a form to input the reviewer ID, decision kind, and optional text/reason
5. Calls `apply_decision` and refreshes the listing

Run with:

```bash
streamlit run -m clinicloop.hitl.console.page
```

## Implementation Details

- All queries use real LangGraph state accessor APIs (`graph.get_state()`, `graph.update_state()`)
- Threads are enumerated with `SELECT DISTINCT thread_id FROM checkpoints`
- Errors reading databases (missing files, corrupt SQLite, missing graph builders) are collected as `ConsoleSourceError` entries and returned alongside successful items
- Items are sorted by interruption timestamp, then agent name, then case ID (ascending)
