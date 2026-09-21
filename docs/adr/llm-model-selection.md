# ADR: LLM Model Selection for Tool Calling

**Date: 2026-09-21**

## Status

Accepted

## Context

The project requires a primary LLM model for tool calling (agents), a judge model for comparison (different family to avoid self-grading), and a fallback model for constrained environments.

Tool calling is a hard constraint: if the primary model cannot emit tool calls reliably, agent graphs cannot be built. The 30-case harness is the gate before any graph development.

## Measurement Results

Real measurements from the 30-case tool-call harness recorded in `evals/results/toolcall/`:

Models measured serially with a warm-up call, one run of 30 cases each. A 28 versus 28 tie is not evidence of a difference.

- **qwen3-30b-a3b-instruct-2507**: 30/30 passing (family: qwen)
- **google/gemma-4-e4b**: 28/30 passing (family: gemma)
- **openai/gpt-oss-20b**: 28/30 passing (family: gpt_oss), failed cases tool_call_023 (by error) and tool_call_030 (no tool call emitted)
- **medgemma-1.5-4b-it**: 0/30 passing (measured and rejected)
- **medgemma-27b-text-it**: 0/30 passing (measured and rejected)

## Alternatives considered

1. **Primary model selection:** qwen3-30b-a3b-instruct-2507 passes all 30 cases with 52.8 tokens/sec.
2. **Judge model selection:** google/gemma-4-e4b from the gemma family (differs from primary's qwen family) with 28/30 passing.
3. **Fallback model selection:** openai/gpt-oss-20b with 28/30 passing and a different family from both primary and judge.

## Decision

### Primary: qwen3-30b-a3b-instruct-2507

- **Model ID:** qwen3-30b-a3b-instruct-2507
- **Family:** qwen
- **Measured Pass Count:** 30 / 30
- **Measured Tokens/Second:** 52.8 tokens/s

Note: Qwen3-30B-A3B-Instruct-2507 Q4_K_M (18.56 GB file, unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF) was downloaded and measured.

### Judge: google/gemma-4-e4b

- **Model ID:** google/gemma-4-e4b
- **Family:** gemma
- **Measured Pass Count:** 28 / 30
- **Measured Tokens/Second:** 42.9 tokens/s

(Judge family `gemma` differs from primary family `qwen`, satisfying the no-self-grading constraint.)

### Fallback: openai/gpt-oss-20b

- **Model ID:** openai/gpt-oss-20b
- **Family:** gpt_oss
- **Measured Pass Count:** 28 / 30
- **Measured Tokens/Second:** 43.5 tokens/s

## Rationale

- The primary model (qwen3-30b-a3b-instruct-2507) passes 30/30 cases, exceeding the promotion bar of 27/30.
- The judge model (google/gemma-4-e4b) from a different family provides independent grading with 28/30 passing.
- The fallback model (openai/gpt-oss-20b) provides a third family option and achieves 28/30 passing.
- All three models demonstrate working tool-calling capability.
- Measurement data is recorded in `evals/results/toolcall/` with per-case results for auditing.

## Consequences

### Positive

- Tool calling is validated with real measurement data from installed models.
- Primary model exceeds the promotion bar with 30/30 cases passing.
- Judge model achieves 28/30 passing from a different family.
- Fallback model achieves 28/30 passing with yet another family.
- All measured models are currently available on this machine.
- Per-case results enable validation and replay without requiring live models.

### Negative

- Judge and fallback models fall below the primary bar of 27/30.
- Model performance may vary based on LM Studio version, hardware load, and quantization.
- Two models (medgemma variants) did not demonstrate tool-calling capability.

## Measurement Audit Trail

- Measurement date: 2026-09-21
- Harness version: 30 fixed cases, deterministic ordering
- Measurement machine: Apple M4 Pro, 48 GB memory
- LM Studio endpoint: http://localhost:1234/v1
- Per-case results recorded in: `evals/results/toolcall/*.jsonl`
- All numbers are from recorded results, deterministically recomputable
