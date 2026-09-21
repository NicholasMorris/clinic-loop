"""Append-only check for guard corpus baseline."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from clinicloop.evals.core.artifacts import AppendOnlyViolation
from clinicloop.evals.core.gitread import git_show as git_show  # noqa: F401


@dataclass
class AppendOnlyResult:
    """Result of an append-only check.

    Attributes:
        first_baseline: True if this is the first baseline (prior absent).
        removed: List of case_ids that were removed.
        reversed: List of case_ids whose verdict was reversed.
    """

    first_baseline: bool
    removed: list[str]
    reversed: list[str]


def append_only_diff(prior: dict[str, str] | None, current: dict[str, str]) -> AppendOnlyResult:
    """Check if current manifest is append-only relative to prior.

    Args:
        prior: Prior manifest (case_id -> verdict). If None, this is first baseline.
        current: Current manifest.

    Returns:
        AppendOnlyResult with first_baseline, removed, and reversed lists.

    Raises:
        AppendOnlyViolation: If removed or reversed violations found.
    """
    if prior is None:
        # First baseline: no prior manifest
        return AppendOnlyResult(first_baseline=True, removed=[], reversed=[])

    # Check for removals (cases in prior but not in current)
    removed = [cid for cid in prior if cid not in current]

    # Check for reversals (same case id but verdict changed)
    reversed_list = [cid for cid in prior if cid in current and prior[cid] != current[cid]]

    if removed or reversed_list:
        msg = f"Append-only violation: removed={removed}, reversed={reversed_list}"
        raise AppendOnlyViolation(msg)

    return AppendOnlyResult(first_baseline=False, removed=[], reversed=[])


GitReader = Callable[[str, str], str | None]


def check_append_only(
    reader: GitReader = git_show,
    base: str = "origin/main",
    manifest_path: Path | None = None,
    write: bool = True,
) -> AppendOnlyResult:
    """Check that corpus is append-only compared to base revision.

    Args:
        reader: GitReader callable to fetch file contents.
        base: Base git revision to compare against.
        manifest_path: Path to manifest.json. If None, uses evals/guard/corpus/manifest.json.
        write: If True and first baseline, write manifest_path.

    Returns:
        AppendOnlyResult.
    """
    import json

    if manifest_path is None:
        corpus_dir = Path(__file__).resolve().parents[4] / "evals" / "guard" / "corpus"
        manifest_path = corpus_dir / "manifest.json"

    # Try to read prior manifest from base revision
    relative_path = str(manifest_path.relative_to(Path.cwd()))
    prior_text = reader(base, relative_path)

    if prior_text is None:
        # No prior manifest on base; this is first baseline
        prior = None
    else:
        prior = json.loads(prior_text)

    # Load current manifest
    from .corpus_loader import load_cases, manifest_of

    cases = load_cases()
    current = manifest_of(cases)

    # Check append-only
    result = append_only_diff(prior, current)

    # Write manifest if first baseline and write=True
    if result.first_baseline and write:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w") as f:
            json.dump(current, f, indent=2)

    return result


def write_manifest(cases: list[Any] | None = None, manifest_path: Path | None = None) -> None:
    """Write the manifest file from cases.

    Args:
        cases: List of GuardCase objects. If None, loads from corpus.
        manifest_path: Path to manifest.json. If None, uses evals/guard/corpus/manifest.json.
    """
    import json

    if cases is None:
        from .corpus_loader import load_cases

        cases = load_cases()

    if manifest_path is None:
        corpus_dir = Path(__file__).resolve().parents[4] / "evals" / "guard" / "corpus"
        manifest_path = corpus_dir / "manifest.json"

    from .corpus_loader import manifest_of

    manifest = manifest_of(cases)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


if __name__ == "__main__":
    import sys

    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"

    result = check_append_only(base=base)
    if result.removed or result.reversed:
        print(f"Append-only violation: removed={result.removed}, reversed={result.reversed}")
        sys.exit(1)
    else:
        print(f"Append-only check passed (first_baseline={result.first_baseline})")
        sys.exit(0)
