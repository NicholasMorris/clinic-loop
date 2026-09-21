"""Replay per-case results from a recorded cassette for deterministic scoring."""

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
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Replay a recorded cassette to reproduce deterministic field values.

    Loads committed per-case results from a cassette file and recalculates
    deterministic scoring fields. Timing fields (latency_ms, tokens_per_second)
    are carried through from the recording.

    Args:
        cassette_path: Path to the cassette JSON file.

    Returns:
        A tuple of (per_case_results, run_summary).

    Raises:
        NotImplementedError: Stub implementation.
    """
    raise NotImplementedError("replay_from_cassette stub")
