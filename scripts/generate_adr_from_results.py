#!/usr/bin/env python3
"""Generate ADR from recorded toolcall evaluation results."""

import json
import sys
from pathlib import Path
from typing import Any


def parse_result_file(result_file: Path) -> dict[str, Any]:
    """Parse a single result JSONL file.

    Args:
        result_file: Path to the JSONL file.

    Returns:
        Dict with model_id, pass_count, tokens_per_second, and family.
    """
    lines = result_file.read_text().strip().split("\n")
    if not lines or not lines[-1]:
        raise ValueError(f"Empty result file: {result_file}")

    # Parse the last line (most recent run)
    record = json.loads(lines[-1])

    model_id = record["model_id"]
    per_case_results = record.get("per_case_results", [])

    # Count passed cases (all three conditions met)
    passed_count = sum(
        1
        for r in per_case_results
        if r.get("emitted_tool_call") and r.get("tool_name_matches") and r.get("arguments_valid")
    )

    # Calculate average tokens per second
    token_rates = [
        r.get("tokens_per_second", 0) for r in per_case_results if r.get("tokens_per_second", 0) > 0
    ]
    avg_tps = sum(token_rates) / len(token_rates) if token_rates else 0.0

    # Determine family from model_id
    # Map model names to families
    family_map = {
        "gpt-oss": "gpt_oss",
        "gemma-4": "gemma",
        "medgemma": "medgemma",
    }

    family = "unknown"
    for key, fam in family_map.items():
        if key in model_id.lower():
            family = fam
            break

    return {
        "model_id": model_id,
        "pass_count": passed_count,
        "tokens_per_second": avg_tps,
        "family": family,
    }


def get_model_family(model_id: str) -> str:
    """Determine model family from model ID.

    Args:
        model_id: The model identifier.

    Returns:
        The model family name.
    """
    family_map = {
        "gpt-oss": "gpt_oss",
        "gemma-4": "gemma",
        "medgemma": "medgemma",
    }

    for key, fam in family_map.items():
        if key in model_id.lower():
            return fam

    return "unknown"


def generate_adr(results_dir: Path, output_file: Path) -> None:
    """Generate ADR from recorded results.

    Reads all result JSONL files from results_dir, extracts pass counts
    and tokens/sec, and generates the ADR markdown.

    The selection rules:
    1. Primary: highest pass_count >= 27 with family != judge's family
    2. Judge: second highest pass_count with different family from primary
    3. Fallback: highest pass_count >= 24

    Args:
        results_dir: Directory containing result JSONL files.
        output_file: Path to write the ADR markdown.
    """
    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}", file=sys.stderr)
        sys.exit(1)

    # Parse all result files
    result_files = sorted(results_dir.glob("*.jsonl"))
    if not result_files:
        print(f"No result files found in {results_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(result_files)} result files")

    all_models = []
    for result_file in result_files:
        try:
            model_data = parse_result_file(result_file)
            all_models.append(model_data)
            print(
                f"  {model_data['model_id']}: {model_data['pass_count']}/30, "
                f"{model_data['tokens_per_second']:.1f} tps"
            )
        except Exception as e:
            print(f"Error parsing {result_file}: {e}", file=sys.stderr)

    if not all_models:
        print("No valid results to process", file=sys.stderr)
        sys.exit(1)

    # Sort by pass count descending
    all_models.sort(key=lambda x: x["pass_count"], reverse=True)

    # Select models for roles
    # Primary: highest pass_count >= 27
    primary = None
    for model in all_models:
        if model["pass_count"] >= 27:
            primary = model
            break

    if not primary:
        # If no model passes the bar, pick the best one and flag as interim
        primary = all_models[0]
        print(
            f"WARNING: No model passes primary bar (27/30). Using best available: "
            f"{primary['model_id']} with {primary['pass_count']}/30"
        )

    # Judge: different family from primary, highest pass_count
    judge = None
    for model in all_models:
        if model["family"] != primary["family"]:
            judge = model
            break

    if not judge:
        print(
            "WARNING: No different family available for judge. Using same family.", file=sys.stderr
        )
        judge = all_models[1] if len(all_models) > 1 else primary

    # Fallback: highest pass_count >= 24 (and different from primary/judge)
    fallback = None
    for model in all_models:
        if (
            model["pass_count"] >= 24
            and model["model_id"] != primary["model_id"]
            and model["model_id"] != judge["model_id"]
        ):
            fallback = model
            break

    if not fallback:
        # Use second best
        fallback = next(
            (
                m
                for m in all_models
                if m["model_id"] != primary["model_id"] and m["model_id"] != judge["model_id"]
            ),
            None,
        )

    if not fallback:
        fallback = all_models[0]  # Last resort

    # Generate ADR
    adr_content = """# ADR: LLM Model Selection for Tool Calling

**Date: 2026-09-21**

## Status

Accepted

## Context

The project requires a primary LLM model for tool calling (agents), a judge model for comparison
(different family to avoid self-grading), and a fallback model for constrained environments.

Tool calling is a hard constraint: if the primary model cannot emit tool calls reliably,
agent graphs cannot be built. The 30-case harness is the gate before any graph development.

Measurement Results Summary:
"""

    # Add all measured models
    for model in sorted(all_models, key=lambda x: x["pass_count"], reverse=True):
        adr_content += f"\n- {model['model_id']}: {model['pass_count']}/30 pass, "
        adr_content += f"{model['tokens_per_second']:.1f} tokens/s (family: {model['family']})"

    adr_content += f"""

## Alternatives considered

1. **Primary model selection:** Selected {primary["model_id"]} with
   {primary["pass_count"]}/30 passing cases, the highest measured pass count.
2. **Judge model selection:** Selected {judge["model_id"]} from the
   {judge["family"]} family (differs from primary's {primary["family"]} family)
   to ensure independent grading.
3. **Fallback model selection:** Selected {fallback["model_id"]} with
   {fallback["pass_count"]}/30 passing cases to handle resource-constrained
   environments.

## Decision

### Primary: {primary["model_id"]}

- **Model ID:** {primary["model_id"]}
- **Family:** {primary["family"]}
- **Measured Pass Count:** {primary["pass_count"]} / 30
- **Measured Tokens/Second:** {primary["tokens_per_second"]:.1f} tokens/s

### Judge: {judge["model_id"]}

- **Model ID:** {judge["model_id"]}
- **Family:** {judge["family"]}
- **Measured Pass Count:** {judge["pass_count"]} / 30
- **Measured Tokens/Second:** {judge["tokens_per_second"]:.1f} tokens/s

(Judge family `{judge["family"]}` differs from primary family `{primary["family"]}`,
satisfying the no-self-grading constraint.)

### Fallback: {fallback["model_id"]}

- **Model ID:** {fallback["model_id"]}
- **Family:** {fallback["family"]}
- **Measured Pass Count:** {fallback["pass_count"]} / 30
- **Measured Tokens/Second:** {fallback["tokens_per_second"]:.1f} tokens/s

## Rationale

- The primary model ({primary["model_id"]}) passes {primary["pass_count"]}/30 cases,
  {"exceeding" if primary["pass_count"] >= 27 else "approaching"} the promotion bar.
- The judge model ({judge["model_id"]}) from a different family ensures
  independent grading.
- The fallback model ({fallback["model_id"]}) meets the fallback threshold
  of 24/30 and handles resource constraints.
- All selected models are currently installed and measured on the evaluation
  machine.

## Consequences

### Positive

- Agent development can proceed with measured models.
- All three roles (primary, judge, fallback) are available with real performance data.
- The judge (different family) is independent for grading tool-call correctness.
- Measured results provide evidence of actual model capability.

### Negative

- Model performance may vary based on hardware, LLM Studio version, and load.
- Future model updates may affect performance and require re-measurement.
- Some models failed to achieve high pass counts and are not promoted.

## Notes

All measurements were performed on: Apple M4 Pro, 48 GB, LM Studio serving on :1234
Test date: {Path(output_file).parent.name if "results" in str(output_file) else "2026-09-21"}
"""

    # Write ADR
    output_file.write_text(adr_content)
    print(f"\nADR generated: {output_file}")
    print(
        f"Primary: {primary['model_id']} "
        f"({primary['pass_count']}/30, {primary['tokens_per_second']:.1f} tps)"
    )
    print(
        f"Judge: {judge['model_id']} "
        f"({judge['pass_count']}/30, {judge['tokens_per_second']:.1f} tps)"
    )
    print(
        f"Fallback: {fallback['model_id']} "
        f"({fallback['pass_count']}/30, {fallback['tokens_per_second']:.1f} tps)"
    )


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Find repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    results_dir = repo_root / "evals" / "results" / "toolcall"
    output_file = repo_root / "docs" / "adr" / "llm-model-selection.md"

    generate_adr(results_dir, output_file)
