"""Tests for triage gate logic: hard gates (AC1) and recompute integration (AC5)."""

import subprocess
from pathlib import Path

import pytest

from evals.triage.gate import run_gate


@pytest.fixture
def passing_fixtures_dir(tmp_path: Path) -> Path:
    """Fixture directory with all-passing artifact cases."""
    fixture_base = Path(__file__).resolve().parent / "fixtures"

    # Copy passing cases
    for i in range(1, 5):
        src = fixture_base / f"passing_case_{i}.json"
        if src.exists():
            dst = tmp_path / src.name
            dst.write_text(src.read_text())

    return tmp_path


def test_recall_one_and_violation_zero_are_hard_gates(
    passing_fixtures_dir: Path,
    tmp_path: Path,
) -> None:
    """AC1: Hard gates require escalation_recall == 1.0 and rule_violation_rate == 0.0.

    On passing fixture: exit code 0, passed=True.
    On seeded-miss fixture: exit code non-zero, failures include escalation_recall and case ID.
    """
    # Test with passing fixtures
    result = run_gate(passing_fixtures_dir)

    assert result.passed, f"Passing fixture should pass: {result.failures}"
    assert result.failures == []

    # Test with seeded-miss fixtures
    miss_dir = Path(__file__).resolve().parent / "fixtures"
    miss_tmp = tmp_path / "miss"
    miss_tmp.mkdir()

    for i in range(1, 4):
        src = miss_dir / f"miss_case_{i}.json"
        if src.exists():
            dst = miss_tmp / src.name
            dst.write_text(src.read_text())

    miss_result = run_gate(miss_tmp)

    assert not miss_result.passed, "Seeded miss should fail the gate"
    assert any("escalation_recall" in f for f in miss_result.failures), (
        f"Should report escalation_recall failure: {miss_result.failures}"
    )
    assert "pass-02" in miss_result.missed_escalation_case_ids, (
        f"Should identify missed escalation case pass-02: {miss_result.missed_escalation_case_ids}"
    )


def test_recompute_and_gate_from_committed_artifacts() -> None:
    """AC5: checks/eval_triage.sh runs recompute and gate on real committed artifacts.

    Run the script as subprocess against the real 6742b288... directory.
    """
    # The worktree root is /Users/nic/.scratch/dispense/wt/M2-6b
    worktree_root = Path(__file__).resolve().parents[3]
    script_path = worktree_root / "checks" / "eval_triage.sh"

    # Check that the script exists
    assert script_path.exists(), f"Script not found: {script_path}"
    assert script_path.stat().st_mode & 0o111, "Script must be executable"

    # Run the script; it should succeed on real committed artifacts
    result = subprocess.run(
        ["bash", str(script_path)],
        cwd=worktree_root,
        capture_output=True,
        text=True,
    )

    # On the real golden set, the gate should pass
    assert result.returncode == 0, (
        f"Gate should pass on real artifacts.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
