"""Recompute triage evaluation artifacts from the golden set and cassette.

This module runs the complete evaluation against the frozen golden set and
cassette, producing candidate artifacts under evals/local/triage/<tree-hash>/
for gate verification. It never reads the committed evals/results/triage/
directory -- that directory is last known-good history, not the thing being
checked. Re-running the real pipeline here is the whole point of a
"recompute" step: it is what lets a regression in the golden set, the
cassette, the runner or the reference reviewer actually surface as a gate
failure, instead of the gate silently re-validating old, already-frozen data.
"""

from pathlib import Path

from clinicloop.compliance.rulesets import load_ruleset
from evals.triage.golden.loader import load_golden_cases, load_intent_elements
from evals.triage.runner import compute_tree_hash, run_all, write_artifacts


def recompute_local(local_out_dir: Path | None = None) -> Path:
    """Re-run the full golden set through the real graph and write candidate artifacts.

    Args:
        local_out_dir: Base directory for candidate output (defaults to evals/local).

    Returns:
        The directory the candidate artifacts were written into
        (local_out_dir/triage/<tree-hash>).
    """
    if local_out_dir is None:
        local_out_dir = Path(__file__).resolve().parents[2] / "evals" / "local"

    cases = load_golden_cases()
    elements = load_intent_elements()
    ruleset = load_ruleset("au")

    artifacts, timings = run_all(cases, ruleset, elements)

    tree_hash = compute_tree_hash(cases, elements)
    out_dir = local_out_dir / "triage" / tree_hash
    write_artifacts(artifacts, out_dir, timings=timings)
    return out_dir


if __name__ == "__main__":
    written_dir = recompute_local()
    print(f"Recomputed {len(list(written_dir.glob('*.json'))) - 1} case artifacts -> {written_dir}")
