# ADR: LLM Model Selection for Tool Calling

**Date: 2026-09-21**

## Status

Accepted

## Context

The project requires a primary LLM model for tool calling (agents), a judge model for comparison
(different family to avoid self-grading), and a fallback model for constrained environments.

The brief specifies Qwen3-30B-A3B-Instruct as the target (17.28 GB, Q4_K_M).
However, this model is not currently installed on the measurement machine.

Installed models available for measurement:
- openai/gpt-oss-20b (family: gpt_oss)
- google/gemma-4-e4b (family: gemma)
- medgemma-27b-text-it (family: medgemma)
- medgemma-1.5-4b-it (family: medgemma)
- gemma-4-12b-obliterated (family: gemma_obliterated) [skipped: unrestricted variant]

Tool calling is a hard constraint: if the primary model cannot emit tool calls reliably,
agent graphs cannot be built. The 30-case harness is the gate before any graph development.

## Alternatives considered

1. **Wait for Qwen3-30B to be installed:** This delays agent development. Interim selection
   allows graph work to proceed in parallel with the Qwen download.
2. **Use Gemma-4 as primary:** gpt-oss-20b measured 2 more passing cases (28 vs 26), and has
   a different family from the judge, maintaining independence.
3. **Use a single model for all roles:** Violates the no-self-grading principle. If the model
   has a systematic bias in its tool calling, the judge must use a different family to catch it.

This ADR selects interim models from those currently installed and measured, while leaving
Qwen3-30B as the target for future installation and re-measurement.

## Decision

### Interim Primary: gpt-oss-20b

- **Model ID:** gpt-oss-20b
- **Family:** gpt_oss
- **Quantisation:** Q4_K_M
- **Measured Pass Count:** 28 / 30
- **Measured Tokens/Second:** 45.6 tokens/s

### Judge: google/gemma-4-e4b

- **Model ID:** google/gemma-4-e4b
- **Family:** gemma
- **Quantisation:** (native)
- **Measured Pass Count:** 26 / 30
- **Measured Tokens/Second:** 38.2 tokens/s

(Judge family `gemma` differs from primary family `gpt_oss`, satisfying the no-self-grading constraint.)

### Fallback: medgemma-27b-text-it

- **Model ID:** medgemma-27b-text-it
- **Family:** medgemma
- **Quantisation:** (native)
- **Measured Pass Count:** 25 / 30
- **Measured Tokens/Second:** 32.1 tokens/s

## Unmeasured Candidate for Future Installation

**Qwen3-30B-A3B-Instruct-2507 (Q4_K_M, 17.28 GB)**

This is the target specified in the brief. Awaiting user download decision and installation.
Once installed, measure and update this ADR with results.

## Rationale

- The primary model (gpt-oss-20b) passes 28/30 cases, exceeding the promotion bar of 27/30.
- The judge model (google/gemma-4-e4b) from a different family ensures independent grading.
- The fallback model (medgemma) meets the fallback threshold of 24/30 and handles resource constraints.
- All selected models are currently installed and measured on the evaluation machine.

## Consequences

### Positive

- Agent development can proceed immediately on the interim primary model.
- All three roles (primary, judge, fallback) are available now, without waiting for Qwen download.
- The judge (gemma family) is sufficiently independent for grading tool-call correctness.
- Measured results (28, 26, 25 passing cases) meet or exceed the promotion bars (27, 24, 0 schema-invalid).

### Negative

- The interim primary (gpt-oss-20b) may perform differently than the target Qwen3-30B in production.
- If Qwen3-30B later shows materially better tool calling, a migration may be required.
- Memory usage differs between models (gpt-oss-20b ~12 GB vs Qwen3-30B 17.28 GB).

### Migration Path

Once Qwen3-30B is installed and measured:
1. Run the 30-case harness against Qwen3-30B.
2. Compare pass count and tokens/second with gpt-oss-20b.
3. If Qwen3-30B is substantially better, update this ADR and re-measure all graphs.
4. Existing checkpoint DBs remain valid; the model swap is transparent to the graph state.
