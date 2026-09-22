"""Gate logic for triage evaluation metrics and thresholds."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

GitReader = Callable[[str, str], str | None]


@dataclass(frozen=True)
class GateResult:
    """Result of running the triage gate.

    Attributes:
        passed: True if all gates passed.
        first_baseline: True if this is the first baseline (no prior thresholds on origin/main).
        failures: List of human-readable failure messages.
        missed_escalation_case_ids: List of case IDs where escalation was missed.
        loosened: List of loosened threshold keys (e.g., 'triage.escalation_recall_min').
    """

    passed: bool
    first_baseline: bool
    failures: list[str]
    missed_escalation_case_ids: list[str]
    loosened: list[str]


def load_candidate_metrics(artifacts_dir: Path) -> dict[str, float]:
    """Load and aggregate metrics from artifacts.

    Args:
        artifacts_dir: Directory containing *.json artifact files.

    Returns:
        Dict with metric names and float values.

    Raises:
        ValueError: If directory is empty or missing.
    """
    raise NotImplementedError("load_candidate_metrics not yet implemented")


def run_gate(
    artifacts_dir: Path,
    thresholds_path: Path | None = None,
    base_revision: str = "origin/main",
    reader: GitReader | None = None,
    local_out_dir: Path | None = None,
) -> GateResult:
    """Run the triage gate against candidate artifacts.

    Args:
        artifacts_dir: Directory with per-case artifact JSON files.
        thresholds_path: Path to thresholds.toml (defaults to evals/triage/thresholds.toml).
        base_revision: Git revision to compare against (default 'origin/main').
        reader: GitReader function for reading from git (default git_show).
        local_out_dir: Directory for writing candidate baseline (default evals/local/).

    Returns:
        GateResult with pass/fail status and details.
    """
    raise NotImplementedError("run_gate not yet implemented")


if __name__ == "__main__":
    import sys

    # When run as a module, operate on the real committed artifacts
    artifacts_dir = Path("evals/results/triage/6742b288454764b8e9934ce1948a22258e7ba7e01228a3e2c45ce61b2749b51e")
    result = run_gate(artifacts_dir)

    for failure in result.failures:
        print(failure)
    for loosened in result.loosened:
        print(f"Loosened: {loosened}")

    sys.exit(0 if result.passed else 1)
