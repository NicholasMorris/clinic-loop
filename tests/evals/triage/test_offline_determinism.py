"""Test offline determinism of triage evaluation."""

import json
from pathlib import Path

import pytest

pytest_socket = pytest.importorskip("pytest_socket")  # noqa: F841


from clinicloop.compliance.rulesets import load_ruleset  # noqa: E402
from evals.triage.golden.loader import load_golden_cases, load_intent_elements  # noqa: E402
from evals.triage.runner import load_artifacts, run_all, write_artifacts  # noqa: E402


@pytest.mark.usefixtures("disable_socket")
def test_cassette_replay_is_offline_and_reproducible(tmp_path: Path) -> None:
    """AC5: Two runs produce byte-identical artifacts (after dropping timings)."""
    cases = load_golden_cases()
    elements = load_intent_elements()
    ruleset = load_ruleset("au")

    # Run all cases once into run1
    run1_dir = tmp_path / "run1"
    artifacts1, timings1_real = run_all(cases, ruleset, elements)
    write_artifacts(artifacts1, run1_dir, timings1_real)

    # Run all cases again into run2
    run2_dir = tmp_path / "run2"
    artifacts2, timings2_real = run_all(cases, ruleset, elements)
    write_artifacts(artifacts2, run2_dir, timings2_real)

    # Load artifacts back from disk
    reloaded1 = load_artifacts(run1_dir)
    reloaded2 = load_artifacts(run2_dir)

    # Compare each artifact (without timings.json)
    for a1, a2 in zip(reloaded1, reloaded2):
        # Convert to dicts and compare
        d1 = a1.model_dump(mode="json")
        d2 = a2.model_dump(mode="json")
        assert d1 == d2, f"Artifacts differ for {a1.case_id}"

    # Separately verify timings.json exists and is well-formed (but don't compare values)
    timings1_path = run1_dir / "timings.json"
    timings2_path = run2_dir / "timings.json"

    assert timings1_path.exists(), "timings.json should exist"
    assert timings2_path.exists(), "timings.json should exist"

    with open(timings1_path) as f:
        timings1 = json.load(f)
    with open(timings2_path) as f:
        timings2 = json.load(f)

    # Verify shape (both should have same case_ids)
    assert set(timings1.keys()) == set(timings2.keys()), "Timings should have same case_ids"

    # Verify all values are numbers (but don't require equality)
    for case_id in timings1:
        assert isinstance(timings1[case_id], (int, float)), (
            f"Timing for {case_id} should be numeric"
        )
        assert isinstance(timings2[case_id], (int, float)), (
            f"Timing for {case_id} should be numeric"
        )
