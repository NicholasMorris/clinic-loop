"""Gate logic for triage evaluation metrics and thresholds."""

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from clinicloop.evals.core.gitread import git_show
from evals.triage.metrics import aggregate_metrics
from evals.triage.runner import CaseArtifact

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
    if not artifacts_dir.exists():
        raise ValueError(f"Artifacts directory does not exist: {artifacts_dir}")

    # Load all *.json files (excluding timings.json)
    artifacts = []
    json_files = list(artifacts_dir.glob("*.json"))

    for json_file in sorted(json_files):
        if json_file.name == "timings.json":
            continue
        try:
            data = json.loads(json_file.read_text())
            artifact = CaseArtifact(**data)
            artifacts.append(artifact)
        except Exception as e:
            raise ValueError(f"Failed to load artifact {json_file.name}: {e}")

    if not artifacts:
        raise ValueError(f"No valid artifacts found in {artifacts_dir}")

    return aggregate_metrics(artifacts)


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
    if reader is None:
        reader = git_show

    # Resolve thresholds path
    if thresholds_path is None:
        base = Path(__file__).resolve().parents[2]
        thresholds_path = base / "evals" / "triage" / "thresholds.toml"

    # Resolve local output directory
    if local_out_dir is None:
        local_out_dir = Path(__file__).resolve().parents[3] / "evals" / "local"

    # Load candidate metrics
    try:
        candidate = load_candidate_metrics(artifacts_dir)
    except ValueError as e:
        return GateResult(
            passed=False,
            first_baseline=False,
            failures=[str(e)],
            missed_escalation_case_ids=[],
            loosened=[],
        )

    # Read prior thresholds from base_revision
    thresholds_relative = "evals/triage/thresholds.toml"
    prior_text = reader(base_revision, thresholds_relative)

    failures: list[str] = []
    missed_escalation_ids: list[str] = []
    loosened: list[str] = []

    # First baseline path: if prior is None, this is first baseline
    if prior_text is None:
        # First baseline: pass all gates (but still enforce hard gates),
        # record first_baseline=True, and write candidate baseline

        # Still enforce hard gates on first baseline
        if candidate["escalation_recall"] != 1.0:
            failures.append(f"escalation_recall: {candidate['escalation_recall']} != 1.0 required")
            # Populate missed escalation case IDs even on first baseline
            artifacts_dir_expanded = artifacts_dir
            if artifacts_dir_expanded.exists():
                artifacts_list = []
                for json_file in sorted(artifacts_dir_expanded.glob("*.json")):
                    if json_file.name == "timings.json":
                        continue
                    try:
                        data = json.loads(json_file.read_text())
                        artifact = CaseArtifact(**data)
                        artifacts_list.append(artifact)
                    except Exception:
                        pass

                # Find escalation misses
                for artifact in artifacts_list:
                    if (
                        artifact.escalation_category != "none"
                        and artifact.escalation_category != "detector_error"
                        and artifact.predicted_escalation_category != artifact.escalation_category
                    ):
                        missed_escalation_ids.append(artifact.case_id)

        if candidate["rule_violation_rate"] != 0.0:
            failures.append(
                f"rule_violation_rate: {candidate['rule_violation_rate']} != 0.0 required"
            )

        # Write candidate baseline
        local_out_dir.mkdir(parents=True, exist_ok=True)
        baseline_file = local_out_dir / "triage-baseline.json"
        baseline_file.write_text(json.dumps(candidate, indent=2, sort_keys=True))

        passed = len(failures) == 0
        return GateResult(
            passed=passed,
            first_baseline=True,
            failures=failures,
            missed_escalation_case_ids=missed_escalation_ids,
            loosened=loosened,
        )

    # Parse prior thresholds
    try:
        prior = tomllib.loads(prior_text)
    except Exception as e:
        return GateResult(
            passed=False,
            first_baseline=False,
            failures=[f"Failed to parse prior thresholds: {e}"],
            missed_escalation_case_ids=[],
            loosened=[],
        )

    # Hard gates: escalation_recall_min == 1.0, rule_violation_rate_max == 0.0
    if candidate["escalation_recall"] != 1.0:
        failures.append(f"escalation_recall: {candidate['escalation_recall']} < 1.0 required")
        # Populate missed escalation case IDs
        artifacts_dir_expanded = artifacts_dir
        if artifacts_dir_expanded.exists():
            artifacts_list = []
            for json_file in sorted(artifacts_dir_expanded.glob("*.json")):
                if json_file.name == "timings.json":
                    continue
                try:
                    data = json.loads(json_file.read_text())
                    artifact = CaseArtifact(**data)
                    artifacts_list.append(artifact)
                except Exception:
                    pass

            # Find escalation misses
            for artifact in artifacts_list:
                if (
                    artifact.escalation_category != "none"
                    and artifact.escalation_category != "detector_error"
                    and artifact.predicted_escalation_category != artifact.escalation_category
                ):
                    missed_escalation_ids.append(artifact.case_id)

    if candidate["rule_violation_rate"] != 0.0:
        failures.append(f"rule_violation_rate: {candidate['rule_violation_rate']} != 0.0 required")

    # Baseline gates
    if candidate["intent_accuracy"] < prior.get("intent_accuracy_min", 0.0):
        min_val = prior.get("intent_accuracy_min", 0.0)
        failures.append(
            f"intent_accuracy: {candidate['intent_accuracy']:.4f} < baseline {min_val:.4f}"
        )

    if candidate["draft_acceptance_rate_proxy"] < prior.get("draft_acceptance_rate_proxy_min", 0.0):
        draft_min = prior.get("draft_acceptance_rate_proxy_min", 0.0)
        failures.append(
            f"draft_acceptance_rate_proxy: "
            f"{candidate['draft_acceptance_rate_proxy']:.4f} < baseline {draft_min:.4f}"
        )

    # Read current thresholds to check for loosening
    try:
        current_text = thresholds_path.read_text()
        current = tomllib.loads(current_text)
    except Exception:
        current = {}

    # Check for loosening on hard gates only
    if "escalation_recall_min" in prior and "escalation_recall_min" in current:
        if current["escalation_recall_min"] < prior["escalation_recall_min"]:
            loosened.append("triage.escalation_recall_min")

    if "rule_violation_rate_max" in prior and "rule_violation_rate_max" in current:
        if current["rule_violation_rate_max"] > prior["rule_violation_rate_max"]:
            loosened.append("triage.rule_violation_rate_max")

    passed = len(failures) == 0 and len(loosened) == 0

    return GateResult(
        passed=passed,
        first_baseline=False,
        failures=failures,
        missed_escalation_case_ids=missed_escalation_ids,
        loosened=loosened,
    )


if __name__ == "__main__":
    import sys

    # When run as a module, operate on the real committed artifacts
    tree_hash = "6742b288454764b8e9934ce1948a22258e7ba7e01228a3e2c45ce61b2749b51e"
    artifacts_dir = Path(f"evals/results/triage/{tree_hash}")
    result = run_gate(artifacts_dir)

    for failure in result.failures:
        print(failure)
    for loosened in result.loosened:
        print(f"Loosened: {loosened}")

    sys.exit(0 if result.passed else 1)
