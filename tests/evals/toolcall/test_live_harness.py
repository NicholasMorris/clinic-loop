"""Live harness tests against real models (requires local_model marker).

These tests call real models via LM Studio and record results.
They are excluded from make ci by the pytest marker and run under make eval-local.
"""

import json
from pathlib import Path

import pytest

from clinicloop.evals.toolcall.cases import load_cases
from clinicloop.evals.toolcall.harness import run_harness
from clinicloop.evals.toolcall.runner import get_installed_models


@pytest.mark.local_model
def test_run_harness_against_all_models() -> None:
    """Run the harness against all installed models and record results.

    This test:
    1. Gets all installed models from LM Studio
    2. For each model, runs the 30-case harness
    3. Records results to evals/results/toolcall/<model-slug>.jsonl
    4. Prints a summary of pass counts and tokens/sec
    """
    # Find output directory
    repo_root = Path(__file__).parent.parent.parent.parent
    output_dir = repo_root / "evals" / "results" / "toolcall"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get models
    models = get_installed_models()
    assert len(models) > 0, "No eligible models found"
    print(f"\nTesting {len(models)} models: {models}")

    # Load cases
    cases = load_cases()
    assert len(cases) == 30, f"Expected 30 cases, got {len(cases)}"

    # Run harness for each model
    for model_id in models:
        print(f"\nTesting: {model_id}")

        per_case_results, run_summary = run_harness(model_id, cases)

        # Compute stats
        passed = run_summary["passed_cases"]
        total = run_summary["total_cases"]
        avg_tps = (
            sum(r.tokens_per_second for r in per_case_results) / len(per_case_results)
            if per_case_results
            else 0.0
        )

        print(f"  Passed: {passed}/{total}")
        print(f"  Avg tokens/sec: {avg_tps:.1f}")

        # Record results
        from datetime import datetime

        output_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model_id": model_id,
            "per_case_results": [
                {
                    "case_id": r.case_id,
                    "model_id": r.model_id,
                    "emitted_tool_call": r.emitted_tool_call,
                    "tool_name_matches": r.tool_name_matches,
                    "arguments_valid": r.arguments_valid,
                    "latency_ms": r.latency_ms,
                    "tokens_per_second": r.tokens_per_second,
                }
                for r in per_case_results
            ],
            "run_summary": run_summary,
        }

        # Save to JSONL (append)
        model_slug = model_id.replace("/", "_").replace(":", "_")
        result_file = output_dir / f"{model_slug}.jsonl"

        with open(result_file, "a") as f:
            f.write(json.dumps(output_record) + "\n")

        print(f"  Saved to: {result_file}")


@pytest.mark.local_model
def test_run_single_model_quick_probe() -> None:
    """Quick probe against one model to verify harness works.

    Tests only the first 3 cases against one model.
    """
    # Load minimal cases
    cases = load_cases()[:3]

    # Test one model
    model_id = "openai/gpt-oss-20b"
    print(f"\nQuick probe: {model_id} with 3 cases")

    per_case_results, run_summary = run_harness(model_id, cases)

    assert len(per_case_results) == 3, f"Expected 3 results, got {len(per_case_results)}"
    assert run_summary["total_cases"] == 3

    for result in per_case_results:
        print(f"  {result.case_id}:")
        print(f"    - emitted_tool_call: {result.emitted_tool_call}")
        print(f"    - tool_name_matches: {result.tool_name_matches}")
        print(f"    - arguments_valid: {result.arguments_valid}")
        print(f"    - tokens/sec: {result.tokens_per_second:.1f}")

    # Assert records have all required fields
    for result in per_case_results:
        assert hasattr(result, "case_id")
        assert hasattr(result, "model_id")
        assert hasattr(result, "emitted_tool_call")
        assert hasattr(result, "tool_name_matches")
        assert hasattr(result, "arguments_valid")
        assert hasattr(result, "latency_ms")
        assert hasattr(result, "tokens_per_second")
