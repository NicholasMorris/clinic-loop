"""P1: Conformance test for dispatch (file glob conflict detection)."""

import json
import subprocess
from pathlib import Path

import pytest


@pytest.mark.checklist_id("P1")
def test_p1_dispatch_detects_overlapping_issues() -> None:
    """P1: dispatch script refuses to open issues with overlapping file globs.

    This test verifies that the dispatch script correctly identifies when two
    GitHub issues have intersecting file ownership patterns and refuses to
    open both simultaneously.
    """
    repo_root = Path(__file__).parent.parent.parent
    dispatch_script = repo_root / "scripts" / "process" / "dispatch.py"
    assert dispatch_script.exists(), f"dispatch script not found at {dispatch_script}"

    # Test case: Two issues with overlapping file globs
    issues = [
        {
            "key": "M0-1",
            "files": ["src/clinicloop/**"],
        },
        {
            "key": "M0-2",
            "files": ["src/clinicloop/world/generator.py"],
        },
    ]

    result = subprocess.run(
        ["python", str(dispatch_script)],
        input=json.dumps(issues),
        capture_output=True,
        text=True,
    )

    # dispatch should reject overlapping globs
    assert result.returncode == 1, (
        f"Expected exit 1 for overlapping globs, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )

    # Output should name both issues
    output = result.stdout + result.stderr
    assert "M0-1" in output and "M0-2" in output, (
        f"Expected both issue keys in output, got: {output}"
    )
