"""Replay per-case results from a recorded cassette for deterministic scoring."""

import json
from pathlib import Path
from typing import Any

# Fields that are deterministic and must match exactly across replays
DETERMINISTIC_FIELDS = [
    "emitted_tool_call",
    "tool_name_matches",
    "arguments_valid",
    "passed_cases",
    "failed_cases",
]


def replay_from_cassette(
    cassette_path: str,
) -> tuple[list[dict[str, Any]], dict[str, Any | int]]:
    """Replay a recorded cassette to reproduce deterministic field values.

    Loads committed per-case results from a cassette file and recalculates
    deterministic scoring fields. Timing fields (latency_ms, tokens_per_second)
    are carried through from the recording.

    Args:
        cassette_path: Path to the cassette JSON file.

    Returns:
        A tuple of (per_case_results, run_summary).

    Raises:
        FileNotFoundError: If the cassette file is not found.
    """
    cassette_file = Path(cassette_path)
    if not cassette_file.exists():
        raise FileNotFoundError(f"Cassette file not found: {cassette_path}")

    with open(cassette_file, "r") as f:
        data = json.load(f)

    per_case_results = data.get("per_case_results", [])
    run_summary = data.get("run_summary", {})

    # Recalculate passed and failed case counts from per-case results
    passed_cases = sum(
        1
        for result in per_case_results
        if result.get("emitted_tool_call")
        and result.get("tool_name_matches")
        and result.get("arguments_valid")
    )
    failed_cases = len(per_case_results) - passed_cases

    # Update run summary with recalculated values
    run_summary["passed_cases"] = passed_cases
    run_summary["failed_cases"] = failed_cases

    return per_case_results, run_summary
