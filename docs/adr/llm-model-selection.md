# ADR: LLM Model Selection for Tool Calling

**Status: Accepted**

**Date: 2026-09-21**

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

## Implications

- Agent graphs build on gpt-oss-20b as the primary model.
- The judge model provides independent verification of tool-call correctness.
- Fallback is available if tool calling degrades under resource pressure.
- Once Qwen3-30B is installed, this ADR will be updated with its measured results.
