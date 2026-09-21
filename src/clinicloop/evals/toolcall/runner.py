"""Runner for the tool-call evaluation harness against live models."""

import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from clinicloop.evals.toolcall.cases import load_cases
from clinicloop.evals.toolcall.harness import run_harness


def get_installed_models(
    base_url: str = "http://localhost:1234/v1",
) -> list[str]:
    """Get list of installed models from LM Studio.

    Args:
        base_url: Base URL for LM Studio API.

    Returns:
        List of model IDs (excluding embedding models and variants).
    """
    models_url = f"{base_url}/models"

    try:
        req = urllib.request.Request(models_url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            model_ids = [model["id"] for model in data.get("data", [])]

            # Filter out embedding models and variants
            # Skip: embedding models, modified/unrestricted variants (with : suffix)
            filtered = []
            for model_id in model_ids:
                if "embed" in model_id.lower() or ":" in model_id:
                    # Skip embedding models and variants
                    continue
                if "obliterated" in model_id.lower():
                    # Skip unrestricted variants
                    continue
                filtered.append(model_id)

            return sorted(filtered)
    except Exception as e:
        raise RuntimeError(f"Failed to get installed models: {e}") from e


def run_evaluation(
    base_url: str = "http://localhost:1234/v1",
    output_dir: str | None = None,
) -> None:
    """Run the evaluation harness against all installed models.

    Saves per-case results and summary for each model to:
    evals/results/toolcall/<model_slug>.jsonl

    Args:
        base_url: Base URL for LM Studio API.
        output_dir: Output directory for results (default: evals/results/toolcall).
    """
    if output_dir is None:
        # Default to evals/results/toolcall relative to repo root
        output_dir = str(
            Path(__file__).parent.parent.parent.parent.parent / "evals" / "results" / "toolcall"
        )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get installed models
    print("Getting installed models...")
    models = get_installed_models(base_url)
    print(f"Found {len(models)} eligible models:")
    for model in models:
        print(f"  - {model}")

    # Load test cases
    print("\nLoading test cases...")
    cases_list: list[dict[str, Any]] = load_cases()  # type: ignore
    print(f"Loaded {len(cases_list)} test cases")

    # Run harness for each model
    print("\nRunning harness for each model...")
    for model_id in models:
        print(f"\n{'=' * 60}")
        print(f"Testing model: {model_id}")
        print(f"{'=' * 60}")

        try:
            start_time = time.time()
            per_case_results, run_summary = run_harness(model_id, cases_list, base_url)
            elapsed = time.time() - start_time

            # Prepare output record
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
                "run_summary": {
                    **run_summary,
                    "total_time_seconds": elapsed,
                },
            }

            # Compute aggregate metrics
            passed = run_summary["passed_cases"]
            total = run_summary["total_cases"]
            avg_latency = (
                sum(r.latency_ms for r in per_case_results) / len(per_case_results)
                if per_case_results
                else 0.0
            )
            avg_tps = (
                sum(r.tokens_per_second for r in per_case_results) / len(per_case_results)
                if per_case_results
                else 0.0
            )

            print("Results:")
            print(f"  Passed: {passed}/{total}")
            print(f"  Avg Latency: {avg_latency:.1f}ms")
            print(f"  Avg Tokens/sec: {avg_tps:.1f}")

            # Save results to JSONL file (one JSON object per line)
            # Use model_id as filename, replacing special characters
            model_slug = model_id.replace("/", "_").replace(":", "_")
            result_file = output_path / f"{model_slug}.jsonl"

            with open(result_file, "a") as f:
                f.write(json.dumps(output_record) + "\n")

            print(f"  Saved to: {result_file}")

        except Exception as e:
            print(f"Error testing model {model_id}: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    run_evaluation()
