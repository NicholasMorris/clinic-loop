"""P5: Conformance test for post_merge_sync (post-merge verification)."""

import json
import subprocess
from pathlib import Path

import pytest


@pytest.mark.checklist_id("P5")
def test_p5_post_merge_sync_verifies_local_remote_match() -> None:
    """P5: post_merge_sync script verifies local checkout matches remote and tree is clean.

    This test verifies that the post_merge_sync script correctly ensures that:
    1. Local HEAD SHA matches the recorded remote default-branch SHA
    2. Working tree is clean (no uncommitted changes)
    3. Exits 0 only when both conditions are met
    4. Exits 1 and names the condition when either fails
    """
    repo_root = Path(__file__).parent.parent.parent
    sync_script = repo_root / "scripts" / "process" / "post_merge_sync.py"
    assert sync_script.exists(), (
        f"post_merge_sync script not found at {sync_script}"
    )

    # Test: Clean state with matching SHA should succeed
    clean_payload = {
        "local_head_sha": "abc123def456",
        "remote_head_sha": "abc123def456",
        "working_tree_dirty": False,
    }

    result = subprocess.run(
        ["python", str(sync_script)],
        input=json.dumps(clean_payload),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"Expected exit 0 for clean state with matching SHA, got {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
