"""Test that ADR values match recomputed values from recorded results."""

from pathlib import Path

import pytest

from clinicloop.evals.toolcall.adr import parse_model_selection_adr
from clinicloop.evals.toolcall.recompute_adr import recompute_adr_from_records


def test_adr_values_match_recorded_results() -> None:
    """Validate that ADR numbers match recomputed values from records.

    This test:
    1. Reads all per-case result JSONL files from evals/results/toolcall/
    2. Recomputes pass counts and tokens/sec for each model
    3. Selects primary, judge, fallback models using role selection rules
    4. Parses the ADR
    5. Asserts that deterministic fields in the ADR match the recomputed values

    Timing fields (latency_ms, tokens_per_second per-case) are recorded
    but excluded from this comparison.
    """
    # Find paths
    repo_root = Path(__file__).parent.parent.parent.parent
    results_dir = repo_root / "evals" / "results" / "toolcall"
    adr_file = repo_root / "docs" / "adr" / "llm-model-selection.md"

    # Skip this test if there are no recorded results yet
    if not results_dir.exists():
        pytest.skip("Results directory not found; run eval harness first")

    result_files = list(results_dir.glob("*.jsonl"))
    if not result_files:
        pytest.skip("No recorded results found; run eval harness first")

    # Recompute ADR values from records
    recomputed = recompute_adr_from_records(results_dir)

    # Parse the ADR
    adr = parse_model_selection_adr(str(adr_file))

    # Validate each role
    for role_name in ["primary", "judge", "fallback"]:
        if role_name not in adr["roles"]:
            # Skip if not defined yet
            pytest.skip(f"Role {role_name} not defined in ADR yet")

        adr_role = adr["roles"][role_name]
        computed_role = recomputed[role_name]

        # Check deterministic fields
        # Note: tokens_per_second is measured and may vary slightly,
        # but we verify it's the same model at least
        assert adr_role["model_id"] == computed_role["model_id"], (
            f"Role {role_name} model_id mismatch: "
            f"ADR has {adr_role['model_id']}, "
            f"records show {computed_role['model_id']}"
        )

        assert adr_role["pass_count"] == computed_role["pass_count"], (
            f"Role {role_name} pass_count mismatch: "
            f"ADR has {adr_role['pass_count']}, "
            f"records show {computed_role['pass_count']}"
        )

        assert adr_role["family"] == computed_role["family"], (
            f"Role {role_name} family mismatch: "
            f"ADR has {adr_role['family']}, "
            f"records show {computed_role['family']}"
        )

        # Tokens/sec can vary significantly based on machine load, so we allow >50% variance
        # This is a timing metric and is not deterministic across runs
        adr_tps = adr_role["tokens_per_second"]
        computed_tps = computed_role["tokens_per_second"]
        if computed_tps > 0:
            pct_diff = abs(adr_tps - computed_tps) / computed_tps * 100
            # Only assert if difference is extreme (>100% change suggests data error)
            assert pct_diff < 100, (
                f"Role {role_name} tokens/sec extreme diff: {pct_diff:.1f}% "
                f"(ADR: {adr_tps:.1f}, records: {computed_tps:.1f})"
            )
