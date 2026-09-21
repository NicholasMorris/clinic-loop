"""AC7 & P4: Fragment check verifies changelog and documentation updates."""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.checklist_id("P4")
def test_fragment_check_exit_codes() -> None:
    """P4: Fragment check exits 1 without both fragment and docs, 0 with both."""
    # Find the fragment check script
    repo_root = Path(__file__).parent.parent.parent
    fragment_check = repo_root / "checks" / "fragment.sh"
    assert fragment_check.exists(), f"Fragment check not found at {fragment_check}"

    # Test 1: No fragment, no docs -> should exit 1
    result = subprocess.run(
        [str(fragment_check), "src/foo.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, (
        f"Expected exit 1 for no fragment/docs, got {result.returncode}:\n{result.stdout}"
    )
    assert "changelog fragment" in result.stdout or "documentation" in result.stdout, (
        f"Expected error about missing fragment or docs, got:\n{result.stdout}"
    )

    # Test 2: Both fragment and docs -> should exit 0
    result = subprocess.run(
        [str(fragment_check), "changes/3.chore.md", "docs/process/ci.md"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Expected exit 0 with fragment and docs, got {result.returncode}:\n{result.stdout}"
    )
