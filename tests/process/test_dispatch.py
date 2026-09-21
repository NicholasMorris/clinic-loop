"""AC2 & AC3: dispatch refuses intersecting file globs between issues."""

import json
import subprocess
from pathlib import Path

import pytest


@pytest.mark.checklist_id("P1")
def test_intersecting_globs_are_refused() -> None:
    """AC2: dispatch exits 1 when two issues have intersecting file globs.

    Verifies:
    - Two issues declaring src/clinicloop/world/** and src/clinicloop/world/generator.py
      should be refused with both issue keys and the intersecting glob in output.
    - Two disjoint issue sets should be accepted with exit 0.
    """
    repo_root = Path(__file__).parent.parent.parent
    dispatch_script = repo_root / "scripts" / "process" / "dispatch.py"
    assert dispatch_script.exists(), f"dispatch not found at {dispatch_script}"

    # Test 1: Intersecting globs should be refused
    issues_intersecting = [
        {
            "key": "M0-1",
            "files": ["src/clinicloop/world/**"],
        },
        {
            "key": "M0-2",
            "files": ["src/clinicloop/world/generator.py"],
        },
    ]

    result = subprocess.run(
        ["python", str(dispatch_script)],
        input=json.dumps(issues_intersecting),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, (
        f"Expected exit 1 for intersecting globs, got {result.returncode}"
    )
    assert "M0-1" in result.stdout or "M0-1" in result.stderr, "Expected M0-1 in output"
    assert "M0-2" in result.stdout or "M0-2" in result.stderr, "Expected M0-2 in output"

    # Test 2: Disjoint globs should be accepted
    issues_disjoint = [
        {
            "key": "M0-1",
            "files": ["src/clinicloop/world/**"],
        },
        {
            "key": "M0-2",
            "files": ["src/clinicloop/api/**"],
        },
    ]

    result = subprocess.run(
        ["python", str(dispatch_script)],
        input=json.dumps(issues_disjoint),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"Expected exit 0 for disjoint globs, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.checklist_id("P1")
def test_per_file_ownership_inside_checks_is_disjoint() -> None:
    """AC3: dispatch treats per-file ownership inside checks/ as disjoint.

    Verifies:
    - Two issues declaring checks/a.sh and checks/b.sh should be accepted (exit 0).
    - One issue declaring checks/** should be refused with the other (exit 1).
    """
    repo_root = Path(__file__).parent.parent.parent
    dispatch_script = repo_root / "scripts" / "process" / "dispatch.py"
    assert dispatch_script.exists(), f"dispatch not found at {dispatch_script}"

    # Test 1: Per-file ownership in checks/ is disjoint
    issues_per_file = [
        {
            "key": "M0-1",
            "files": ["checks/a.sh"],
        },
        {
            "key": "M0-2",
            "files": ["checks/b.sh"],
        },
    ]

    result = subprocess.run(
        ["python", str(dispatch_script)],
        input=json.dumps(issues_per_file),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"Expected exit 0 for per-file checks/, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )

    # Test 2: checks/** should conflict with per-file ownership
    issues_glob_conflict = [
        {
            "key": "M0-1",
            "files": ["checks/a.sh"],
        },
        {
            "key": "M0-2",
            "files": ["checks/**"],
        },
    ]

    result = subprocess.run(
        ["python", str(dispatch_script)],
        input=json.dumps(issues_glob_conflict),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, (
        f"Expected exit 1 for checks/** conflicting with per-file, got {result.returncode}"
    )
    assert "M0-1" in result.stdout or "M0-1" in result.stderr
    assert "M0-2" in result.stdout or "M0-2" in result.stderr
