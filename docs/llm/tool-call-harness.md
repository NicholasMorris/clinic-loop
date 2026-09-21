# Tool-Call Harness

The tool-call evaluation harness measures whether installed LLM models can correctly emit tool calls with valid arguments. This is a prerequisite: agent graphs build on top of models that pass this harness, so we measure tool calling before building any agent.

## Case Set

The harness runs 30 fixed test cases, each with:

- **Case ID**: Unique identifier
- **Tool Name**: Expected tool to call (e.g., `get_weather`, `send_email`)
- **Tool Schema**: JSON schema for expected arguments
- **Prompt**: The LLM prompt for this case

Cases are diverse:
- Simple string/number arguments
- Complex nested objects
- Arrays and required vs optional fields
- Different tool names (query, create, delete, etc.)

The case set is fully deterministic: loading it twice yields identical ordered case IDs.

## Scoring Rules

For each case, the harness records three deterministic booleans:

- **`emitted_tool_call`**: The model produced syntactically valid JSON with a `tool_name` field.
- **`tool_name_matches`**: The tool name equals the expected tool name (only meaningful if `emitted_tool_call` is True).
- **`arguments_valid`**: The arguments dict matches the expected JSON schema.

A case is counted as **passed** if all three are True. If the model returns plain prose or invalid JSON, all three are False, and the case is counted as **failed** (no exception is raised).

## Per-Case Result

Each result record includes:

- `case_id`
- `model_id`
- `emitted_tool_call` (bool)
- `tool_name_matches` (bool)
- `arguments_valid` (bool)
- `latency_ms` (float) — wall time to generate the response
- `tokens_per_second` (float) — generation speed
- `passed_cases` (int in summary) — count of cases where all three deterministic fields are True
- `failed_cases` (int in summary) — count of remaining cases

## Deterministic vs Timing Fields

The harness splits recorded results into two categories:

### Deterministic Fields

These are reproducible from the model's logic and are compared exactly across replays:

```python
DETERMINISTIC_FIELDS = [
    "emitted_tool_call",
    "tool_name_matches",
    "arguments_valid",
    "passed_cases",
    "failed_cases",
]
```

When replaying from a cassette file (e.g., in CI after a local measurement run), these fields are recomputed from the model response and must match the committed values exactly.

### Timing Fields

These depend on the machine's load and are carried through from the recording without comparison:

- `latency_ms`
- `tokens_per_second`

## Promotion Bar

The promotion bar is configured in `evals/toolcall/thresholds.toml`:

```toml
primary_min_passing_cases = 27      # out of 30
fallback_min_passing_cases = 24     # out of 30
max_schema_invalid_outputs = 0      # no tolerance
```

A model is promoted to:

- **`primary`**: If it passes >= 27 cases with zero schema-invalid outputs.
- **`fallback`**: If it passes >= 24 cases with zero schema-invalid outputs.
- **Not recommended**: If it passes < 24 cases or has any schema-invalid outputs.

These thresholds are **assumed starting values** and may be revised based on measured results. The values live in the config file, not in code, so the bar can be updated without changing the harness logic.

## Local Measurement

To measure a model locally:

```bash
make eval-local
```

This:

1. Loads the installed models from `models.toml`.
2. Runs the 30-case harness against each model role (primary, judge, fallback).
3. Records per-case results and a summary in `evals/results/toolcall/<tree-hash>/`.
4. Calculates tokens/second and latency.

Results are JSON files, one per model, with structure:

```json
{
  "per_case_results": [
    {
      "case_id": "tool_call_001",
      "model_id": "primary",
      "emitted_tool_call": true,
      "tool_name_matches": true,
      "arguments_valid": true,
      "latency_ms": 123.45,
      "tokens_per_second": 45.6
    },
    ...
  ],
  "run_summary": {
    "passed_cases": 28,
    "failed_cases": 2,
    ...
  }
}
```

## CI Replay

The local gate (`make ci`) recomputes deterministic scoring fields from committed per-case files:

```bash
checks/eval_toolcall.sh
```

This:

1. Loads the committed per-case results.
2. Recalculates `emitted_tool_call`, `tool_name_matches`, and `arguments_valid` from the model response.
3. Verifies all deterministic fields match exactly.
4. Excludes timing fields from comparison (they vary by machine load).

This proves that:

- **Scoring is consistent**: The same model response scores the same way every time.
- **No data fabrication**: If someone edited a committed file, CI will catch it.
- **CI does not require a running model**: Replay uses only the committed cassettes.

## ADR: Model Selection

The file `docs/adr/llm-model-selection.md` records:

- Which model was chosen as **primary** for agent graphs, with its pass count and measured tokens/second.
- Which model was chosen as **judge** (different family, for independent grading).
- Which model was chosen as **fallback** (constrained resource environment).
- Why those choices were made.

The primary's pass count must be >= `promotion_bar().primary_min_passing_cases`.
The judge's family must differ from the primary's family (so nothing grades itself).

## Further Reading

- **Test cases**: `src/clinicloop/evals/toolcall/cases.py`
- **Scoring logic**: `src/clinicloop/evals/toolcall/harness.py`
- **Cassette replay**: `src/clinicloop/evals/toolcall/replay.py`
- **Configuration**: `evals/toolcall/thresholds.toml`
- **Model selection ADR**: `docs/adr/llm-model-selection.md`
