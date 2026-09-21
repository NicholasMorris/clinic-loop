"""Append-only check for guard corpus baseline."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from clinicloop.evals.core.artifacts import AppendOnlyViolation


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


def append_only_diff(
    prior: dict[str, str] | None, current: dict[str, str]
) -> AppendOnlyResult:
    """Check if current manifest is append-only relative to prior.

    Args:
        prior: Prior manifest (case_id -> verdict). If None, this is first baseline.
        current: Current manifest.

    Returns:
        AppendOnlyResult with first_baseline, removed, and reversed lists.

    Raises:
        AppendOnlyViolation: If removed or reversed violations found.
        NotImplementedError: Stub not yet implemented.
    """
    raise NotImplementedError("append_only_diff stub")


GitReader = Callable[[str, str], str | None]


def git_show(revision: str, path: str) -> str | None:
    """Read a file from a git revision via git show.

    Args:
        revision: Git revision (e.g., 'origin/main', 'HEAD').
        path: Path to file in the repository.

    Returns:
        File contents as string, or None if revision or path doesn't exist.
    """
    raise NotImplementedError("git_show stub")


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

    Raises:
        NotImplementedError: Stub not yet implemented.
    """
    raise NotImplementedError("check_append_only stub")
