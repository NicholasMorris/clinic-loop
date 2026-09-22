"""Tests for first-baseline handling (AC4)."""

import json
from pathlib import Path

from evals.triage.gate import run_gate


def test_absent_on_origin_main_passes_and_records_candidate_baseline(
    tmp_path: Path,
) -> None:
    """AC4: On first baseline (absent on origin/main), gate passes and records baseline.

    With a stub git reader reporting that evals/triage/thresholds.toml and the
    triage registry entry are absent on origin/main, the gate exits 0, reports
    first_baseline true, and writes the current metric values as the candidate
    baseline under evals/local/triage-baseline.json without modifying
    evals/triage/thresholds.toml.
    """
    fixture_base = Path(__file__).resolve().parent / "fixtures"

    # Stub reader that returns None for any git read (nothing on origin/main)
    def stub_reader(revision: str, path: str) -> str | None:
        return None

    # Create passing fixture cases
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    for i in range(1, 5):
        src = fixture_base / f"passing_case_{i}.json"
        if src.exists():
            dst = fixture_dir / src.name
            dst.write_text(src.read_text())

    # Create a thresholds file (local, not on origin/main)
    thresholds_path = tmp_path / "thresholds.toml"
    thresholds_path.write_text("""
escalation_recall_min = 1.0
rule_violation_rate_max = 0.0
intent_accuracy_min = 0.95
draft_acceptance_rate_proxy_min = 0.85
""")

    # Create local output directory
    local_out_dir = tmp_path / "local_out"
    local_out_dir.mkdir()

    # Run gate with stub reader returning None (first baseline)
    result = run_gate(
        fixture_dir,
        thresholds_path=thresholds_path,
        base_revision="origin/main",
        reader=stub_reader,
        local_out_dir=local_out_dir,
    )

    # Should pass and report first_baseline
    assert result.passed, f"First baseline should pass: {result.failures}"
    assert result.first_baseline is True, "Should report first_baseline=True"

    # Should have written baseline file
    baseline_file = local_out_dir / "triage-baseline.json"
    assert baseline_file.exists(), f"Should create {baseline_file}"

    baseline_data = json.loads(baseline_file.read_text())
    assert "intent_accuracy" in baseline_data
    assert "escalation_recall" in baseline_data
    assert "rule_violation_rate" in baseline_data
    assert "draft_acceptance_rate_proxy" in baseline_data
