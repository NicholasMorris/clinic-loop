#!/usr/bin/env python3
"""Verify local checkout matches remote and working tree is clean after merge.

Reads a JSON payload from stdin containing:
- local_head_sha: The SHA of the local HEAD
- remote_head_sha: The SHA of the remote default branch HEAD
- working_tree_dirty: Boolean indicating if the working tree has uncommitted changes

Verifies that:
1. local_head_sha == remote_head_sha
2. working_tree_dirty is False

Exit codes:
- 0: Local matches remote and tree is clean
- 1: Divergent HEAD or dirty tree
- 2: Stub implementation (not yet implemented)

Output format:
On error (exit 1), prints which condition failed (divergent HEAD or dirty tree).
"""

import json
import sys


def check_sync(payload: dict) -> int:
    """Check that local checkout matches remote and tree is clean.

    Args:
        payload: Dictionary with local_head_sha, remote_head_sha, working_tree_dirty

    Returns:
        0 if synced and clean, 1 if divergent or dirty, 2 if stub
    """
    raise NotImplementedError("post_merge_sync not yet implemented")


if __name__ == "__main__":
    try:
        payload = json.load(sys.stdin)
        exit_code = check_sync(payload)
        sys.exit(exit_code)
    except NotImplementedError:
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
