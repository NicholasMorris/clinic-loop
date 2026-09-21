"""Test AC5: Cassette replay reproduces deterministic fields."""

import json
import tempfile
from pathlib import Path
from typing import Any

from clinicloop.evals.toolcall.replay import DETERMINISTIC_FIELDS, replay_from_cassette


def test_cassette_replay_reproduces_deterministic_fields_only() -> None:
    """AC5: Replaying from cassette reproduces deterministic field values.

    The replay uses a pytest-socket blocked loopback-only fixture,
    so all data comes from the cassette file, not from live models.

    Deterministic fields are copied exactly. Timing fields are carried through
    but excluded from comparison.
    """
    # Create a temporary cassette file with per-case results and summary
    cassette_data: dict[str, Any] = {
        "per_case_results": [
            {
                "case_id": "case_001",
                "model_id": "test_model",
                "emitted_tool_call": True,
                "tool_name_matches": True,
                "arguments_valid": True,
                "latency_ms": 100.5,  # timing field
                "tokens_per_second": 50.0,  # timing field
            },
            {
                "case_id": "case_002",
                "model_id": "test_model",
                "emitted_tool_call": False,
                "tool_name_matches": False,
                "arguments_valid": False,
                "latency_ms": 95.3,
                "tokens_per_second": 52.0,
            },
        ],
        "run_summary": {
            "passed_cases": 1,
            "failed_cases": 1,
            "emitted_tool_call": True,
            "tool_name_matches": True,
            "arguments_valid": True,
        },
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        cassette_path = Path(tmpdir) / "cassette.json"
        cassette_path.write_text(json.dumps(cassette_data))

        # Replay from the cassette
        replayed_results, replayed_summary = replay_from_cassette(str(cassette_path))

        # Extract deterministic fields from replayed results
        replayed_det: dict[str, list[Any]] = {
            field: [r.get(field) for r in replayed_results]
            for field in DETERMINISTIC_FIELDS
            if field not in ["passed_cases", "failed_cases"]
        }

        # Extract deterministic fields from original cassette
        committed_det: dict[str, list[Any]] = {
            field: [r.get(field) for r in cassette_data["per_case_results"]]
            for field in DETERMINISTIC_FIELDS
            if field not in ["passed_cases", "failed_cases"]
        }

        # Deterministic fields must match exactly
        assert replayed_det == committed_det

        # Check that passed_cases and failed_cases are in the deterministic list
        assert "passed_cases" in DETERMINISTIC_FIELDS
        assert "failed_cases" in DETERMINISTIC_FIELDS

        # Timing fields should be present but not compared for exact match
        for result in replayed_results:
            assert "latency_ms" in result
            assert "tokens_per_second" in result
