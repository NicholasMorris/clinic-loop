"""AC4: No-loosening check against base revision, in both directions."""

from pathlib import Path

import pytest

from clinicloop.evals.core.thresholds import check_no_loosening, compare_thresholds


@pytest.mark.checklist_id("E2")
def test_loosened_threshold_fails_in_both_directions() -> None:
    """Higher-is-better dropping and lower-is-better rising are loosened; stricter is fine."""
    higher = compare_thresholds(
        "toolcall", "primary_min_passing_cases = 27", "primary_min_passing_cases = 20"
    )
    assert higher.loosened == ["toolcall.primary_min_passing_cases"]

    lower = compare_thresholds("guard", "rule_violation_rate = 0.0", "rule_violation_rate = 0.01")
    assert lower.loosened == ["guard.rule_violation_rate"]

    stricter_higher = compare_thresholds(
        "toolcall", "primary_min_passing_cases = 20", "primary_min_passing_cases = 27"
    )
    stricter_lower = compare_thresholds(
        "guard", "rule_violation_rate = 0.05", "rule_violation_rate = 0.0"
    )
    assert stricter_higher.loosened == [] and stricter_lower.loosened == []


@pytest.mark.checklist_id("E2")
def test_check_no_loosening_exit_code_uses_the_reader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The exit code is 1 when the head revision loosens a committed threshold, else 0."""
    (tmp_path / "evals" / "demo").mkdir(parents=True)
    (tmp_path / "evals" / "demo" / "thresholds.toml").write_text("rule_violation_rate = 0.0\n")
    monkeypatch.chdir(tmp_path)

    def loosened_reader(revision: str, path: str) -> str | None:
        return (
            "rule_violation_rate = 0.0\n" if revision == "base" else "rule_violation_rate = 0.2\n"
        )

    def equal_reader(revision: str, path: str) -> str | None:
        return "rule_violation_rate = 0.0\n"

    assert check_no_loosening("base", "head", reader=loosened_reader) == 1
    assert check_no_loosening("base", "head", reader=equal_reader) == 0
