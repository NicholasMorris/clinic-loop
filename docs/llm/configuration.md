# LLM Configuration

## Overview

All agents in this repository talk to a local LM Studio server without API keys or hosted inference. Configuration is centralized in a single `models.toml` file at the repository root.

Every configuration declares exactly four required model roles:
- `primary` — the agent's preferred model for reasoning and tool calling
- `judge` — a separate model family for scoring or reviewing outputs (never the same family as primary)
- `fallback` — a smaller model for structured output when the primary model fails tool calling
- `fake` — an in-process stub model for offline testing (no network, no GPU)

## File Format

The configuration file is a TOML file with a table for each role:

```toml
[primary]
kind = "server"
repo_id = "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF"
revision = "eea7b2be5805a5f151f8847ede8e5f9a9284bf77"
quant = "Q4_K_M"
family = "qwen"
base_url = "http://127.0.0.1:1234/v1"
structured_method = "tools"
parallel_tool_calls = true
reasoning_handling = "enabled"
context_window = 8000
temperature = 0.7
seed = 42

[judge]
kind = "server"
# ... same fields

[fallback]
kind = "server"
# ... same fields

[fake]
kind = "fake"
family = "fake"
structured_method = "tools"
temperature = 0.7
seed = 42
```

## Server Rows

Each server row represents a model loaded by LM Studio. Required fields:

| Field | Type | Purpose |
|-------|------|---------|
| `kind` | `"server"` | Discriminator; marks this as a remote model |
| `repo_id` | string | Hugging Face model ID (e.g., `unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF`) |
| `revision` | string | Pinned commit SHA (e.g., `eea7b2be58...`); `"main"` is rejected |
| `quant` | string | Quantisation (e.g., `Q4_K_M`); empty string is rejected |
| `family` | string | Model family for documentation (e.g., `qwen`, `gpt_oss`) |
| `base_url` | string | OpenAI-compatible endpoint (e.g., `http://127.0.0.1:1234/v1`) |
| `structured_method` | `"tools"` or `"json_schema"` | How to extract structured output (see below) |
| `parallel_tool_calls` | boolean | Whether to allow multiple tool calls in one response |
| `reasoning_handling` | string | Handling of reasoning tokens (e.g., `"enabled"`, `"disabled"`) |
| `context_window` | integer | Model's context window size in tokens |
| `temperature` | float | Sampling temperature; **no default** — must be explicit |
| `seed` | integer | Random seed for reproducibility; **no default** — must be explicit |

### Loopback Constraint

Server rows must use a loopback address only:
- `127.0.0.1` (IPv4)
- `::1` (IPv6)
- `localhost` (hostname, resolves to loopback)

Any other hostname or IP address (e.g., `192.168.1.100`, `example.com`) is rejected at configuration time with `NonLoopbackBaseURL`.

### Pinning Rules

- **revision**: Must be a commit SHA, not a branch name like `main`. Pinning ensures reproducibility.
- **quant**: Must not be empty. The quantisation format (e.g., `Q4_K_M`, `Q6_K`) must be specified.

## Fake Row

The `fake` role provides an in-process mock model for offline testing of agent logic. It does not connect to any server and opens no sockets.

Required fields for `fake`:

| Field | Type |
|-------|------|
| `kind` | `"fake"` |
| `family` | string (any value; conventionally `"fake"`) |
| `structured_method` | `"tools"` or `"json_schema"` |
| `temperature` | float |
| `seed` | integer |

Forbidden fields (will raise `FakeRowHasServerFields` if present):
- `repo_id`
- `revision`
- `quant`
- `base_url`

The fake model is used only in tests marked with `@pytest.mark.local_model` that override the real LM Studio connection. Example:

```python
@pytest.mark.local_model
def test_agent_logic_offline():
    fake_model = build_chat_model("fake")
    fake_model.set_responses(["Yes", "No"])
    # ... use fake_model in agent without network access
```

## Structured Output Methods

Agents extract structured data (JSON, Pydantic models) using the method declared in the config row. Two methods are supported:

### `tools` (Tool Calling)

When `structured_method = "tools"`:
- The model's tool-calling capability is used to enforce structured output.
- The request includes a JSON schema of the expected tool.
- If tool calling fails or the model cannot generate a valid tool call, the system falls back to JSON schema (see below) and retries exactly once.
- This retry is transparent: the function still returns the parsed schema and records that `json_schema` was used as a fallback.

### `json_schema` (Constrained JSON)

When `structured_method = "json_schema"`:
- The LM Studio grammar (powered by Outlines) enforces a JSON schema directly.
- No tool calling is involved.
- If the schema is invalid or the model cannot satisfy it, an error is raised (no automatic fallback).

### Fallback Behavior

If a row declares `structured_method = "tools"` but the first attempt fails:
1. **Attempt 1** uses tool calling (the configured method).
2. **Attempt 2** uses JSON schema as a fallback.
3. If both fail, the error propagates to the caller.
4. The global `structured_method_used` is set to whichever method succeeded (or last attempted).

## Factory and Configuration Loading

### `load_models_config(config_path)`

Loads and validates `models.toml`:

```python
from clinicloop.llm.config import load_models_config

config = load_models_config(Path("models.toml"))
# Raises MissingModelRole if primary, judge, fallback, or fake is missing.
# Raises NonLoopbackBaseURL if any server row has a non-loopback URL.
# Raises FakeRowHasServerFields if fake has repo_id, revision, quant, or base_url.
# Raises ValidationError if pinning rules are violated or fields are missing.
```

### `build_chat_model(role)`

Creates a ChatOpenAI instance from the config for a given role:

```python
from clinicloop.llm.factory import build_chat_model

model_primary = build_chat_model("primary")  # ChatOpenAI
model_fake = build_chat_model("fake")  # FakeChatModel

# Raises UnknownModelRole if role is not in {primary, judge, fallback, fake}.
```

### `structured_output(model, schema, prompt)`

Extracts structured output from a model:

```python
from clinicloop.llm.structured import structured_output
from pydantic import BaseModel


class MySchema(BaseModel):
    name: str
    value: int


result = structured_output(model_primary, MySchema, "Extract data from: ...")
# Returns an instance of MySchema.
# If tool calling fails and json_schema is configured as fallback, it retries exactly once.
# The global structured_method_used is updated to record which method succeeded.
```

## Future Changes

Model selection and configuration are intentionally separated from agent logic. Agents call `build_chat_model(role)` and let the factory handle all configuration details.

- **M0-6 (`make doctor`)** recommends model choices based on available RAM but does not write `models.toml`.
- **A sequenced edit issue after M0-7a** will copy M0-6's recommendation into the `primary` and `fallback` rows.
- Additional rows may be added for new components via sequenced edit issues (shared-file rule: every change to this file is owned by exactly one issue).

This design ensures:
- No two open issues edit `models.toml` in parallel.
- Changing models requires only editing the config file, not agent code.
- Tests can swap models by providing a different `models.toml` without changing any test code.

## Troubleshooting

### `NonLoopbackBaseURL`

The server row's `base_url` is not loopback. Check the host:
- Use `127.0.0.1` or `localhost` for local LM Studio on the same machine.
- Use `::1` for IPv6 loopback (rare).

### `MissingModelRole`

One of the required roles is missing from the config file. Ensure all four are present:
- `[primary]`
- `[judge]`
- `[fallback]`
- `[fake]`

### `UnknownModelRole`

You called `build_chat_model` with a role name not in the above list. Use one of the four standard roles.

### `FakeRowHasServerFields`

The `[fake]` row contains a field that only server rows should have (`repo_id`, `revision`, `quant`, or `base_url`). Remove it.

### `ValidationError` on `revision` or `quant`

- `revision` is the string `"main"` → Use a pinned commit SHA instead.
- `quant` is empty → Specify a quantisation format (e.g., `Q4_K_M`).

## See Also

- `src/clinicloop/llm/` — Implementation (config loader, factory, structured output, fake model)
- `tests/llm/` — Unit tests for all requirements
- `tests/conformance/test_L2.py` — Loopback constraint conformance test
- `tests/conformance/test_L7.py` — Model swapping conformance test
