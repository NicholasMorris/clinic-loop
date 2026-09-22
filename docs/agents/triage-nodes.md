# Triage nodes and state

The triage agent reads inbound patient messages, redacts personally identifiable information, classifies message intent, calls tools with state-bound identifiers, drafts replies, and runs guard checks before and after human review. All steps are pure functions operating on `TriageState`, a validated pydantic model carrying case identity, the redacted thread, detected language, classified intent, escalation status, tool calls, draft text, guard verdicts, and human decisions.

## TriageState

The state object is a pydantic v2 `BaseModel` with strict validation, immutable nested types, and serialization that supports round-tripping through JSON.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `case_id` | `str` | Required | Unique case identifier. |
| `patient_id` | `str` | Required | Unique patient identifier. |
| `order_id` | `str \| None` | `None` | Order identifier (optional for non-order queries). |
| `redacted_thread` | `list[Turn]` | `[]` | List of redacted messages (patient + assistant). |
| `patient_data_block` | `str` | `""` | Delimited patient text (prevents instruction injection). |
| `language` | `Literal["en", "other"] \| None` | `None` | Detected language after ingest. |
| `intent` | `Intent \| None` | `None` | Classified intent after classify_intent. |
| `escalation_category` | `str \| None` | `None` | Escalation result (e.g., "clinical", "misuse"). |
| `escalation_clear` | `EscalationClear \| None` | `None` | HMAC-authenticated token for draft gate. |
| `tool_calls` | `list[ToolCall]` | `[]` | Recorded tool calls with results. |
| `draft` | `str \| None` | `None` | Generated reply text (or `None` if routed). |
| `guard_verdicts` | `list[dict]` | `[]` | Guard check results (regulatory + final). |
| `human_decision` | `HumanDecision \| None` | `None` | Approval decision (approve / edit / reject). |
| `routing_reason` | `str \| None` | `None` | Why the case was routed (e.g., "language", "rule_block"). |
| `routing_rule_ids` | `tuple[str, ...]` | `()` | Rule IDs that caused routing. |

### Nested types

#### Turn

A single message in the redacted thread (frozen, immutable).

```python
class Turn(BaseModel):
    model_config = ConfigDict(frozen=True)
    role: Literal["patient", "assistant"]
    text: str
```

#### ToolCall

A recorded tool call with arguments bound from state and its result summary.

```python
class ToolCall(BaseModel):
    name: str  # Tool name (e.g., "get_order_status")
    args: dict[str, str]  # Arguments (patient_id, order_id from state)
    result_summary: str  # Short factual summary of result
```

### Enums

#### Intent

The classified intent of the patient message. The enum has 11 members.

```python
class Intent(str, Enum):
    unknown = "unknown"  # Cannot classify or out of scope
    general_question = "general_question"
    order_status = "order_status"
    cancellation = "cancellation"
    delivery_problem = "delivery_problem"
    account_inquiry = "account_inquiry"
    adverse_event = "adverse_event"
    suspected_misuse = "suspected_misuse"
    mental_health_distress = "mental_health_distress"
    pregnancy_related = "pregnancy_related"
    not_a_patient_message = "not_a_patient_message"
```

Intents `adverse_event`, `suspected_misuse`, `mental_health_distress`, and `pregnancy_related` trigger escalation and never receive a draft; they are routed immediately to a clinician queue.

### Validation

- `extra="forbid"`: No undeclared fields allowed.
- `validate_assignment=True`: Assignments to fields are validated immediately.
- Enum fields raise `pydantic.ValidationError` if assigned an invalid value.
- `EscalationClear` is authenticated and raises `EscalationClearForbidden` on construction if the HMAC is invalid.

### Serialization

The state round-trips through `model_dump_json()` → `json.loads()` → `model_validate()` with full equality, including:
- The complete `EscalationClear` token (as `text_sha256` and `mac` fields)
- All `GuardVerdict` objects (as dicts with jurisdiction, version, rule IDs)
- `HumanDecision` (with action and edited text)

No raw PII survives serialization; all identifiers are either state fields (patient_id, order_id, case_id) or pseudonymized via `redact_with_pseudonyms()`.

## Nodes

Each node is a pure function from state (as a `dict` for type flexibility during graph execution) to a state update `dict`. Nodes are testable without a compiled graph and return only the fields they modify.

### ingest(state, raw_message, run_key)

**Purpose:** Redact PII from raw patient message and detect language.

**Inputs:**
- `raw_message`: Unredacted patient message (e.g., from API request body).
- `run_key`: Consistent key for pseudonym hashing within this case (e.g., case_id).

**Process:**
1. Call `redact_with_pseudonyms(raw_message, run_key)` to detect identifiers and replace with pseudonymous tokens.
2. Detect language via `detect_language(redacted_text)`.
3. Build delimited patient-data block via `build_data_block(redacted_text)`.
4. Create redacted thread with a single `Turn(role="patient", text=redacted)`.

**Returns:**
```python
{
    "redacted_thread": [Turn(role="patient", text=redacted)],
    "patient_data_block": str,  # Delimited
    "language": "en" | "other",
}
```

**Safety:** The raw message is never stored in state or logs. All downstream references to patient text come from the redacted thread.

### classify_intent(state, model)

**Purpose:** Classify the patient message intent using an LLM.

**Inputs:**
- `state["patient_data_block"]`: Delimited patient text (from ingest).
- `model`: `ModelPort` with `complete(prompt, *, sample_index=0) -> str` method.

**Process:**
1. Build prompt via `build_classify_prompt(state["patient_data_block"])`.
2. Call `model.complete(prompt, sample_index=0)`.
3. Parse JSON response (strip code fences; extract first `{...}` if there is leading prose).
4. Extract `intent` field; validate against `Intent` enum.
5. On parse failure or invalid intent name, return `Intent.unknown`.

**Returns:**
```python
{"intent": Intent}
```

**Model independence:** The prompt and response format are defined statically; no model name appears in the code. Model selection is controlled by the caller via the `models.toml` row passed to `ModelPort`.

### resolve(state, model, tools)

**Purpose:** Call tools for order-related intents (order_status, cancellation, delivery_problem).

**Inputs:**
- `state["intent"]`: Classified intent.
- `state["patient_id"]`: State-held patient identifier.
- `state["order_id"]`: State-held order identifier (may be `None`).
- `model`: `ModelPort` for prompting which tool to call.
- `tools`: `ToolRunner` protocol with `run(name, patient_id, order_id) -> str`.

**Process:**
1. If intent is not in `{order_status, cancellation, delivery_problem}`, return `{}` (no tool call).
2. Prompt the model: "For the patient intent, which tool should be called?" List available tools.
3. Parse JSON response for `tool` name and ignore any `args` in the response.
4. Validate tool name against known tools: `get_order_status`, `list_patient_orders`.
5. Call `tools.run(tool_name, state["patient_id"], state["order_id"])`.
6. Record the call with **state-bound IDs** (not model-suggested IDs).

**Returns:**
```python
{"tool_calls": [ToolCall(name=str, args={"patient_id": str, "order_id": str}, result_summary=str)]}
# or {} if intent does not need tools
```

**Security:** Tool arguments are bound from state, never chosen by the model. A model cannot exfiltrate or manipulate patient/order IDs.

### draft(state, model)

**Purpose:** Generate a reply draft with escalation and language checks.

**Inputs:**
- `state["language"]`: Detected language ("en" or "other").
- `state["escalation_clear"]`: `EscalationClear` token (or `None`).
- `state["redacted_thread"]`: Redacted message thread.
- `state["tool_calls"]`: Any tool results.
- `model`: `ModelPort` for generating the draft.

**Process:**
1. **Language check first:** If `language == "other"`, return `{"routing_reason": "language"}` with no draft and no model call.
2. **Escalation check:** Call `escalation.gate.require_clear(thread_dicts, state["escalation_clear"])`.
   - Raises `EscalationRequired` if the token is missing or its `text_sha256` differs from the thread hash.
   - This gate prevents drafting without explicit escalation clearance (M2-3).
3. **Draft generation:** Build prompt with thread, tool results, and hard rules (English only; no clinical/dosing advice; never name medicines; never claim conditions; be brief and polite).
4. Call `model.complete(prompt, sample_index=0)` and strip whitespace.

**Returns:**
```python
{
    "draft": str  # Generated reply
}
# or
{"routing_reason": "language"}  # If non-English
```

**Raises:** `EscalationRequired` if the escalation token is missing or mismatches.

### regulatory_guard(state, ruleset)

**Purpose:** Run the guard core on the draft before human approval.

**Inputs:**
- `state["redacted_thread"]`: Redacted message thread.
- `state["draft"]`: Generated draft (or empty string if routed).
- `ruleset`: `Ruleset` object with jurisdiction, version, and rule definitions.

**Process:**
1. Build thread as list of dicts: `[{"role": "patient", "text": ...}, {"role": "assistant", "text": draft}]`.
2. Call `compliance.guard.core.check(thread, ruleset.jurisdiction, ruleset)`.
3. Convert returned `GuardVerdict` to a dict and append to `state["guard_verdicts"]`.
4. If verdict is blocked (`allowed == False`), set `routing_reason = "rule_block"` and `routing_rule_ids = tuple(verdict.rule_ids)`.

**Returns:**
```python
{
    "guard_verdicts": [... existing ..., {allowed, rule_ids, jurisdiction, ...}]
}
# or if blocked:
{
    "guard_verdicts": [...],
    "routing_reason": "rule_block",
    "routing_rule_ids": (rule_id, rule_id, ...)
}
```

### guard_final(state, ruleset)

**Purpose:** Re-check the exact post-edit text after human review.

**Inputs:**
- `state["human_decision"]`: `HumanDecision` with action (approve / edit / reject) and optional edited text.
- `state["redacted_thread"]`: Redacted thread.
- `state["draft"]`: Original draft (fallback if human approved without editing).
- `ruleset`: `Ruleset` object.

**Process:**
1. Require `state["human_decision"]` is not `None` (raise `ValueError` otherwise).
2. Determine final text: if action is "edit", use `edited_text`; otherwise use `draft`.
3. Build thread as list of dicts with final text as the assistant message.
4. Call `compliance.guard.core.check(thread, ruleset.jurisdiction, ruleset)`.
5. Append verdict to `guard_verdicts` and set routing if blocked.

**Returns:**
```python
{
    "guard_verdicts": [... existing ..., final verdict],
}
# or if blocked:
{
    "guard_verdicts": [...],
    "routing_reason": "rule_block",
    "routing_rule_ids": (...)
}
```

**Raises:** `ValueError` if `human_decision` is `None`.

## Delimited patient-data contract

The `patient_data_block` field isolates patient text from instruction fields. It is built by `build_data_block()` as:

```
[DELIMITED_DATA]
<redacted_patient_text>
[/DELIMITED_DATA]
```

The delimiters `[DELIMITED_DATA]` and `[/DELIMITED_DATA]` are fixed and are included in prompts so that instructions inside patient text are parsed as data, not executable instructions.

## EscalationClear token

The `escalation_clear` field holds an HMAC-authenticated token (`EscalationClear`) that proves an escalation check was run and passed for the current thread. The token is:

- **Minted by** `compliance.escalation.detector.detect()` after escalation checks pass.
- **Validated on** `draft()` via `compliance.escalation.gate.require_clear()`.
- **Serializable:** Stored as a dataclass with `text_sha256` (SHA-256 of the thread) and `mac` (HMAC-SHA256 signed with a per-machine key).
- **Per-machine:** The signing key is read from `$CLINICLOOP_ESCALATION_KEY` environment variable, or stored in `var/keys/escalation.key` (created on first use, 32 random hex bytes, chmod 600).
- **Security model:** This token authenticates against accidental or model-driven forgery on a single machine. It is **not a boundary against a local attacker who can read the key file**; the README documents this.

No draft can be generated without an `EscalationClear` token matching the redacted thread.

## Model decoupling

None of the nodes contain model names, row names from `models.toml`, or imports from `langchain_openai`. Model selection is controlled entirely by the caller:

1. Caller loads `models.toml` and picks a row (e.g., "primary", "judge").
2. Caller builds a `ModelPort` via the factory.
3. Caller passes the `ModelPort` to nodes (ingest, classify_intent, resolve, draft).
4. Nodes call `model.complete(prompt, *, sample_index=0)` and consume the response.

Swapping rows (e.g., from Qwen3-30B to a smaller model) requires no changes to node code.

## Testing

### Cassette-based testing

The `classify_intent` and `resolve` nodes are tested against cassettes keyed by:

- Model ID (e.g., "unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF")
- Prompt hash (SHA-256 of the prompt)
- Sample index (0, 1, 2, ...)
- Seed

A cassette is a JSONL file where each line is `{prompt_hash, model_id, sample_index, response}`. The `CassetteModelPort` loads cassettes and raises `CassetteMiss` if a prompt is not recorded.

Tests run offline with cassette replay; no live model calls are made.

### Fixtures

- `tests/agents/triage_nodes/fixtures/intent_threads.jsonl`: 50 hand-written, labelled intent messages.
- `tests/agents/triage_nodes/cassettes/recorded_intent.jsonl`: 50 real responses from the Qwen3-30B-A3B-Instruct model (recorded once, append-only).
- `tests/agents/triage_nodes/cassettes/synthetic_tool_binding.jsonl`: One synthetic adversarial cassette line for testing that model-suggested IDs are ignored.

### Honesty

The intent cassette (`recorded_intent.jsonl`) is a real recording of 50 hand-written, fairly clear-cut messages classified by a live Qwen3 model in a single pass. It is **not** a claim that the same model achieves this accuracy on real traffic; the dataset is small, curated for clarity, and biased toward common intents. Tests using this cassette verify that the parsing and enum handling are correct, not that the model is production-ready.

The tool-binding cassette is entirely synthetic and is used only to verify that tool arguments come from state, not from model output.

The language detection heuristic is simple (ASCII-letter threshold, stopword check) and may fail on code-switched messages, transliterated names, or mixed-script text. Edge cases are listed in the test suite.

Token limits on the Qwen3-30B-A3B-Instruct model are 8,000 input + output. The draft prompt includes the full thread; long conversations may exceed context. The graph layer (M2-5b) will handle truncation and fallback.
