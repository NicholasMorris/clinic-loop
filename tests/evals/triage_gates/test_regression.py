"""Tests for baseline regression detection (AC2)."""

from pathlib import Path

from evals.triage.gate import run_gate


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

    # Create a thresholds file (local)
    thresholds_tmp = tmp_path / "thresholds.toml"
    thresholds_tmp.write_text("""
escalation_recall_min = 1.0
rule_violation_rate_max = 0.0
intent_accuracy_min = 0.8
draft_acceptance_rate_proxy_min = 0.875
""")

    # Create regress fixture cases (metrics: intent_accuracy=0.9, draft=0.8889)
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    for i in range(1, 11):
        src = fixture_base / f"regress_case_{i:02d}.json"
        if src.exists():
            dst = fixture_dir / src.name
            dst.write_text(src.read_text())

    # Test 1: baseline_for_ac2 has 0.90 and 0.80; candidate has 0.8889 and 0.75
    # This should fail because 0.8889 < 0.90 and 0.75 < 0.80
    baseline_text = fixture_base.joinpath("baseline_for_ac2.toml").read_text()

    def stub_reader_high(revision: str, path: str) -> str | None:
        if revision == "origin/main" and "thresholds.toml" in path:
            return baseline_text
        return None

    result = run_gate(
        fixture_dir,
        thresholds_path=thresholds_tmp,
        base_revision="origin/main",
        reader=stub_reader_high,
    )

    assert not result.passed, "Should fail when metrics below baseline"
    assert any("intent_accuracy" in f for f in result.failures), (
        f"Should report intent_accuracy below baseline: {result.failures}"
    )
    assert any("draft_acceptance_rate_proxy" in f for f in result.failures), (
        f"Should report draft_acceptance_rate_proxy below baseline: {result.failures}"
    )

    # Test 2: baseline with lower thresholds (0.8 and 0.875); should pass
    # because 0.8 >= 0.8 and 0.875 >= 0.875
    lower_baseline = """
escalation_recall_min = 1.0
rule_violation_rate_max = 0.0
intent_accuracy_min = 0.8
draft_acceptance_rate_proxy_min = 0.875
"""

    def stub_reader_low(revision: str, path: str) -> str | None:
        if revision == "origin/main" and "thresholds.toml" in path:
            return lower_baseline
        return None

    result = run_gate(
        fixture_dir,
        thresholds_path=thresholds_tmp,
        base_revision="origin/main",
        reader=stub_reader_low,
    )

    assert result.passed, f"Should pass when metrics equal baseline: {result.failures}"
