"""Tests for the checks/fragment.sh changelog and documentation check."""

import subprocess
from pathlib import Path

CHECK = Path(__file__).resolve().parents[2] / "checks" / "fragment.sh"

FRAGMENT_MESSAGE = "changelog fragment"
DOCS_MESSAGE = "documentation"


def run_check(*names: str, labels: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run checks/fragment.sh against a fixture list of changed file names.

    Args:
        *names: The changed paths against the merge base.
        labels: An optional comma-separated label list.

    Returns:
        The completed process.
    """
    command = [str(CHECK)]
    if labels is not None:
        command += ["--labels", labels]
    return subprocess.run([*command, *names], capture_output=True, text=True, check=False)


def test_fragment_and_docs_are_required_unless_labelled() -> None:
    """AC8: exit 1 naming the unmet requirement, exit 0 with both or with no-changelog."""
    assert CHECK.is_file(), "checks/fragment.sh is missing"

    neither = run_check("src/clinicloop/a.py")
    assert neither.returncode == 1, neither.stdout + neither.stderr
    assert FRAGMENT_MESSAGE in neither.stdout and DOCS_MESSAGE in neither.stdout

    docs_only = run_check("src/clinicloop/a.py", "docs/process/shared-files.md")
    assert docs_only.returncode == 1
    assert FRAGMENT_MESSAGE in docs_only.stdout and DOCS_MESSAGE not in docs_only.stdout

    fragment_only = run_check("src/clinicloop/a.py", "changes/12.feat.md")
    assert fragment_only.returncode == 1
    assert DOCS_MESSAGE in fragment_only.stdout and FRAGMENT_MESSAGE not in fragment_only.stdout

    for kind in ("feat", "fix", "docs", "chore", "test"):
        both = run_check(f"changes/7.{kind}.md", "docs/index.md")
        assert both.returncode == 0, f"{kind}: {both.stdout}"

    for bad in (
        "changes/7.bogus.md",
        "changes/x.feat.md",
        "changes/7.feat.txt",
        "changes/README.md",
    ):
        rejected = run_check(bad, "docs/index.md")
        assert rejected.returncode == 1, f"{bad} was accepted as a fragment"
        assert FRAGMENT_MESSAGE in rejected.stdout

    assert run_check("src/clinicloop/a.py", labels="no-changelog").returncode == 0
    assert run_check("src/clinicloop/a.py", labels="bug, no-changelog").returncode == 0
    assert run_check("src/clinicloop/a.py", labels="bug,no-changelogs").returncode == 1
    assert run_check("src/clinicloop/a.py", labels="bug").returncode == 1

    skipped = run_check()
    assert skipped.returncode == 0 and "skipped" in skipped.stdout.lower()
