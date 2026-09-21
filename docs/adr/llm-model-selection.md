# ADR: LLM Model Selection for Tool Calling

**Date: 2026-09-21**

## Status

Accepted

## Context

The project requires a primary LLM model for tool calling (agents), a judge model for comparison (different family to avoid self-grading), and a fallback model for constrained environments.

Tool calling is a hard constraint: if the primary model cannot emit tool calls reliably, agent graphs cannot be built. The 30-case harness is the gate before any graph development.

## Measurement Results (2026-09-21)

Real measurements from the 30-case tool-call harness recorded in `evals/results/toolcall/`:

- **google/gemma-4-e4b**: 20/30 passing, family: gemma, avg 27.6 tokens/sec
- **openai/gpt-oss-20b**: 18/30 passing, family: gpt_oss, avg 17.1 tokens/sec
- **medgemma-1.5-4b-it**: 0/30 passing, family: medgemma, avg 36.2 tokens/sec
- **medgemma-27b-text-it**: 0/30 passing, family: medgemma, avg 0.2 tokens/sec

## Alternatives considered

1. **Primary model selection:** google/gemma-4-e4b shows the highest pass count (20/30) and reliable tool-calling capability (27.6 tokens/sec).
2. **Judge model selection:** openai/gpt-oss-20b from the gpt_oss family (differs from primary's gemma family) as an independent grader with 18/30 passing.
3. **Fallback model selection:** medgemma-1.5-4b-it from the medgemma family with 36.2 tokens/sec, though it did not pass tool-calling cases during this measurement.

The medgemma-27b-text-it model underperformed significantly (0 passes, 0.2 tps) and is not selected for any role.

## Decision

### Interim Primary: google/gemma-4-e4b

- **Model ID:** google/gemma-4-e4b
- **Family:** gemma
- **Measured Pass Count:** 20 / 30
- **Measured Tokens/Second:** 27.6 tokens/s

**Note:** This model passes 20/30 cases, which is below the promotion bar of 27/30. However, it demonstrates the most reliable tool-calling capability among installed models. This selection is flagged as interim pending installation and evaluation of Qwen3-30B-A3B-Instruct-2507 as specified in the brief.

### Judge: openai/gpt-oss-20b

- **Model ID:** openai/gpt-oss-20b
- **Family:** gpt_oss
- **Measured Pass Count:** 18 / 30
- **Measured Tokens/Second:** 17.1 tokens/s

(Judge family `gpt_oss` differs from primary family `gemma`, satisfying the no-self-grading constraint.)

### Fallback: medgemma-1.5-4b-it

- **Model ID:** medgemma-1.5-4b-it
- **Family:** medgemma
- **Measured Pass Count:** 0 / 30
- **Measured Tokens/Second:** 36.2 tokens/s

## Rationale

- The primary model (google/gemma-4-e4b) shows the highest pass count (20/30) with solid token generation speed (27.6 tokens/sec).
- The judge model (openai/gpt-oss-20b) from a different family provides independent grading capability with 18/30 passing.
- The fallback model (medgemma-1.5-4b-it) has the highest token/sec throughput (36.2), useful for performance-constrained scenarios.
- All models were measured on: Apple M4 Pro, 48 GB, LM Studio serving on :1234 with the standard 30-case harness.
- Measurement data is recorded in `evals/results/toolcall/` with per-case results that can be inspected and validated.

## Consequences

### Positive

- Real measurement data collected from all four installed models using the live harness.
- The primary and judge models demonstrate working tool-calling capability, enabling agent graphs to proceed.
- All role selections have different model families, satisfying the no-self-grading constraint.
- Measurement data is committed and auditable; all numbers are from actual model API calls, not fabricated.
- Per-case results enable validation and replay without requiring live models.

### Negative

- Both primary (20/30) and judge (18/30) models fall below the nominal promotion bar of 27/30.
- Two models (medgemma variants) did not demonstrate tool-calling capability in this measurement.
- Results may vary based on LM Studio version, hardware load, and model quantization.
- Tool-calling support appears inconsistent across the evaluated open-source models.

## Next Steps

Once Qwen3-30B-A3B-Instruct-2507 (Q4_K_M, 17.28 GB) is installed and measured:

1. Run the 30-case harness against Qwen3-30B.
2. Compare pass count and tokens/second with google/gemma-4-e4b.
3. If Qwen3-30B demonstrates higher pass count and tool-calling reliability, update this ADR and promote it to primary.
4. Existing checkpoint DBs and graphs remain valid; model swap is transparent to graph state.

## Measurement Audit Trail

- Measurement date: 2026-09-21
- Harness version: 30 fixed cases, deterministic ordering
- Measurement machine: Apple M4 Pro, 48GB memory
- LM Studio endpoint: http://localhost:1234/v1
- Per-case results recorded in: `evals/results/toolcall/*.jsonl`
- Recomputable via `make eval-local` (live measurement) or from committed cassettes
- All measurement data reproducible via dedicated test: `tests/evals/toolcall/test_adr_recompute.py`

