"""Tests for threshold loosening detection (AC3)."""

from pathlib import Path

from evals.triage.gate import run_gate


def test_threshold_loosening_against_origin_main_fails(
    tmp_path: Path,
) -> None:
    """AC3: Loosening hard-gate thresholds causes the gate to fail.

    With synthetic origin/main snapshot holding escalation_recall 1.0 and
    rule_violation_rate 0.0, the gate exits non-zero and returns loosened
    when the local threshold is lowered to 0.95. With both values unchanged,
    returns loosened == [] with exit 0.
    """
    fixture_base = Path(__file__).resolve().parent / "fixtures"
    baseline_path = fixture_base / "baseline_for_ac3.toml"
    baseline_text = baseline_path.read_text()

    def stub_reader(revision: str, path: str) -> str | None:
        if revision == "origin/main" and "thresholds.toml" in path:
            return baseline_text
        return None

    # Create passing fixture cases
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_base_files = fixture_base / "passing_case_1.json"
    if fixture_base_files.exists():
        dst = fixture_dir / "case_1.json"
        dst.write_text(fixture_base_files.read_text())

    # Test 1: Loosen escalation_recall_min to 0.95
    thresholds_tmp = tmp_path / "thresholds.toml"
    thresholds_tmp.write_text("""
escalation_recall_min = 0.95
rule_violation_rate_max = 0.0
""")

    result = run_gate(
        fixture_dir,
        thresholds_path=thresholds_tmp,
        base_revision="origin/main",
        reader=stub_reader,
    )

    assert not result.passed, "Should fail when escalation_recall loosened"
    assert "triage.escalation_recall_min" in result.loosened, \
        f"Should flag triage.escalation_recall_min as loosened: {result.loosened}"

    # Test 2: Keep both values unchanged
    thresholds_tmp.write_text("""
escalation_recall_min = 1.0
rule_violation_rate_max = 0.0
""")

    result = run_gate(
        fixture_dir,
        thresholds_path=thresholds_tmp,
        base_revision="origin/main",
        reader=stub_reader,
    )

    assert result.passed, "Should pass when thresholds unchanged"
    assert result.loosened == [], \
        f"Should have no loosened entries: {result.loosened}"
