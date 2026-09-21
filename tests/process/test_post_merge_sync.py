"""AC6: post_merge_sync checks that local HEAD matches remote and tree is clean."""

import json
import subprocess
from pathlib import Path

import pytest


@pytest.mark.checklist_id("P5")
def test_divergent_head_or_dirty_tree_fails() -> None:
    """AC6: post-merge sync exits 1 when HEAD diverges from remote or tree is dirty.

    Verifies:
    - When local HEAD SHA differs from recorded remote default-branch SHA: exit 1
    - When working tree is dirty: exit 1
    - Output names which condition was met
    """
    repo_root = Path(__file__).parent.parent.parent
    sync_script = repo_root / "scripts" / "process" / "post_merge_sync.py"
    assert sync_script.exists(), f"post_merge_sync not found at {sync_script}"

    # Test 1: Divergent HEAD should fail
    divergent_payload = {
        "local_head_sha": "abc123",
        "remote_head_sha": "def456",
        "working_tree_dirty": False,
    }

    result = subprocess.run(
        ["python", str(sync_script)],
        input=json.dumps(divergent_payload),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, f"Expected exit 1 for divergent HEAD, got {result.returncode}"
    assert (
        "divergent" in result.stdout.lower()
        or "divergent" in result.stderr.lower()
        or "HEAD" in result.stdout
        or "HEAD" in result.stderr
    ), "Expected mention of divergent HEAD in output"

    # Test 2: Dirty tree should fail
    dirty_payload = {
        "local_head_sha": "abc123",
        "remote_head_sha": "abc123",
        "working_tree_dirty": True,
    }

    result = subprocess.run(
        ["python", str(sync_script)],
        input=json.dumps(dirty_payload),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, f"Expected exit 1 for dirty tree, got {result.returncode}"
    assert (
        "dirty" in result.stdout.lower()
        or "dirty" in result.stderr.lower()
        or "tree" in result.stdout.lower()
        or "tree" in result.stderr.lower()
    ), "Expected mention of dirty tree in output"

    # Test 3: Clean and matching should succeed
    clean_payload = {
        "local_head_sha": "abc123",
        "remote_head_sha": "abc123",
        "working_tree_dirty": False,
    }

    result = subprocess.run(
        ["python", str(sync_script)],
        input=json.dumps(clean_payload),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"Expected exit 0 for clean tree and matching SHA, "
        f"got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
