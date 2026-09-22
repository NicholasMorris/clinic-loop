"""Tests for baseline regression detection (AC2)."""

from pathlib import Path

import pytest

from evals.triage.gate import GateResult, run_gate


def test_metric_below_origin_main_baseline_fails_the_gate(
    tmp_path: Path,
) -> None:
    """AC2: Baseline gates fail when candidate < prior baseline.

    With synthetic origin/main baseline of intent_accuracy 0.90 and
    draft_acceptance_rate_proxy 0.80, the gate exits non-zero naming the metric
    when the candidate reports 0.89 or 0.79, and exits 0 when the candidate
    reports 0.90 and 0.80.
    """
    fixture_base = Path(__file__).resolve().parent / "fixtures"
    baseline_path = fixture_base / "baseline_for_ac2.toml"

    # Stub git reader that returns the fixture baseline
    baseline_text = baseline_path.read_text()

    def stub_reader(revision: str, path: str) -> str | None:
        if revision == "origin/main" and "thresholds.toml" in path:
            return baseline_text
        return None

    # Create a thresholds file with lower values than baseline
    thresholds_tmp = tmp_path / "thresholds.toml"
    thresholds_tmp.write_text("""
escalation_recall_min = 1.0
rule_violation_rate_max = 0.0
intent_accuracy_min = 0.89
draft_acceptance_rate_proxy_min = 0.79
""")

    # Create passing fixture cases
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_base_files = fixture_base / "passing_case_1.json"
    if fixture_base_files.exists():
        dst = fixture_dir / "case_1.json"
        dst.write_text(fixture_base_files.read_text())

    # Run gate with stub reader; should fail on both metrics
    result = run_gate(
        fixture_dir,
        thresholds_path=thresholds_tmp,
        base_revision="origin/main",
        reader=stub_reader,
    )

    assert not result.passed, "Should fail when metrics below baseline"
    assert any("intent_accuracy" in f for f in result.failures), \
        f"Should report intent_accuracy below baseline: {result.failures}"
    assert any("draft_acceptance_rate_proxy" in f for f in result.failures), \
        f"Should report draft_acceptance_rate_proxy below baseline: {result.failures}"

    # Now test with candidate values equal to baseline; should pass
    thresholds_tmp.write_text("""
escalation_recall_min = 1.0
rule_violation_rate_max = 0.0
intent_accuracy_min = 0.90
draft_acceptance_rate_proxy_min = 0.80
""")

    result = run_gate(
        fixture_dir,
        thresholds_path=thresholds_tmp,
        base_revision="origin/main",
        reader=stub_reader,
    )

    assert result.passed, f"Should pass when metrics equal baseline: {result.failures}"
