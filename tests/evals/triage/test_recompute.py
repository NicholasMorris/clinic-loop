"""Test that aggregate metrics can be recomputed from written artifacts."""

from pathlib import Path

from clinicloop.compliance.rulesets import load_ruleset
from evals.triage.golden.loader import load_golden_cases, load_intent_elements
from evals.triage.metrics import aggregate_metrics
from evals.triage.runner import load_artifacts, run_all, write_artifacts


def test_aggregate_equals_recomputation_from_per_case_artifacts(tmp_path: Path) -> None:
    """AC2: Artifacts written to disk can be recomputed to equal the aggregate reported."""
    cases = load_golden_cases()
    elements = load_intent_elements()
    ruleset = load_ruleset("au")

    # Run all cases
    artifacts, timings = run_all(cases, ruleset, elements)

    # Compute aggregate from artifacts
    aggregate_reported = aggregate_metrics(artifacts)

    # Write artifacts to disk
    output_dir = tmp_path / "run1"
    write_artifacts(artifacts, output_dir, timings)

    # Reload artifacts from disk
    recomputed_artifacts = load_artifacts(output_dir)

    # Compute aggregate from reloaded artifacts
    aggregate_recomputed = aggregate_metrics(recomputed_artifacts)

    # Verify they're equal field by field
    assert set(aggregate_reported.keys()) == set(aggregate_recomputed.keys()), (
        f"Keys differ: {aggregate_reported.keys()} vs {aggregate_recomputed.keys()}"
    )

    for key in aggregate_reported.keys():
        reported_val = aggregate_reported[key]
        recomputed_val = aggregate_recomputed[key]
        assert reported_val == recomputed_val, (
            f"Metric {key} differs: reported={reported_val}, recomputed={recomputed_val}"
        )
