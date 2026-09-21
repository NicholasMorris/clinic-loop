"""Recompute ADR values from recorded toolcall results."""

import json
from pathlib import Path
from typing import Any


def recompute_adr_from_records(
    results_dir: str | Path,
) -> dict[str, Any]:
    """Recompute ADR model selection from recorded results.

    Reads all result JSONL files, recomputes pass counts and tokens/sec,
    and returns the values that should appear in the ADR.

    Args:
        results_dir: Directory containing result JSONL files.

    Returns:
        Dict with keys: primary, judge, fallback, each containing:
        - model_id: str
        - pass_count: int
        - tokens_per_second: float
        - family: str
    """
    results_dir = Path(results_dir)

    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    result_files = sorted(results_dir.glob("*.jsonl"))
    if not result_files:
        raise FileNotFoundError(f"No result files found in {results_dir}")

    # Parse all result files
    all_models: dict[str, dict[str, Any]] = {}

    for result_file in result_files:
        lines = result_file.read_text().strip().split("\n")
        if not lines or not lines[-1]:
            continue

        # Parse all runs and find the best (highest pass count)
        best_record = None
        best_pass_count = -1

        for line in lines:
            if not line.strip():
                continue
            record = json.loads(line)
            per_case_results = record.get("per_case_results", [])

            passed_count = sum(
                1
                for r in per_case_results
                if r.get("emitted_tool_call")
                and r.get("tool_name_matches")
                and r.get("arguments_valid")
            )

            if passed_count > best_pass_count:
                best_pass_count = passed_count
                best_record = record

        if best_record is None:
            continue

        model_id = best_record["model_id"]
        per_case_results = best_record.get("per_case_results", [])

        # Count passed cases (all three conditions met)
        passed_count = sum(
            1
            for r in per_case_results
            if r.get("emitted_tool_call")
            and r.get("tool_name_matches")
            and r.get("arguments_valid")
        )

        # Calculate average tokens per second
        token_rates = [
            r.get("tokens_per_second", 0)
            for r in per_case_results
            if r.get("tokens_per_second", 0) > 0
        ]
        avg_tps = sum(token_rates) / len(token_rates) if token_rates else 0.0

        # Determine family from model_id
        family = _get_model_family(model_id)

        all_models[model_id] = {
            "model_id": model_id,
            "pass_count": passed_count,
            "tokens_per_second": avg_tps,
            "family": family,
        }

    if not all_models:
        raise ValueError("No valid results to process")

    # Sort by pass count descending, then by model_id for deterministic tie-breaking
    sorted_models = sorted(
        all_models.values(),
        key=lambda x: (-x["pass_count"], x["model_id"])
    )

    # Select models for roles
    primary = sorted_models[0]

    # Judge: different family from primary, highest pass_count
    judge = None
    for model in sorted_models:
        if model["family"] != primary["family"]:
            judge = model
            break

    if not judge:
        # If no different family, use second best
        judge = sorted_models[1] if len(sorted_models) > 1 else primary

    # Fallback: prefer different from primary/judge
    fallback = None
    for model in sorted_models:
        if model["model_id"] != primary["model_id"] and model["model_id"] != judge["model_id"]:
            fallback = model
            break

    if not fallback:
        fallback = sorted_models[-1] if len(sorted_models) > 1 else primary

    return {
        "primary": primary,
        "judge": judge,
        "fallback": fallback,
    }


def _get_model_family(model_id: str) -> str:
    """Determine model family from model ID.

    Args:
        model_id: The model identifier.

    Returns:
        The model family name (lowercase, underscores).
    """
    model_lower = model_id.lower()

    # Check more specific patterns first to avoid false matches
    if "medgemma" in model_lower:
        return "medgemma"
    elif "gpt-oss" in model_lower or "gpt_oss" in model_lower:
        return "gpt_oss"
    elif "gemma-4" in model_lower or "gemma 4" in model_lower:
        return "gemma"
    elif "qwen" in model_lower:
        return "qwen"
    elif "gemma" in model_lower:
        return "gemma"

    return "unknown"
