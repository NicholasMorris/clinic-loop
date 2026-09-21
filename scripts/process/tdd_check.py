#!/usr/bin/env python3
"""Check that a commit follows test-first discipline (red commit).

Verifies that:
1. The commit adds at least one file under a tests/ path
2. The added tests fail for one of exactly two accepted reasons:
   - AssertionError from a test
   - NotImplementedError raised from a stub under src/
3. Rejects commits where tests fail for other reasons (collection errors,
   ImportError, SyntaxError, NameError, AttributeError)

Exit codes:
- 0: Red commit is valid (tests fail for accepted reasons)
- 1: Red commit is invalid (wrong failure reason or no tests added)
- 2: Stub implementation (not yet implemented)
"""

import sys


def check_red_commit(repo_path: str, commit_sha: str) -> int:
    """Check that a commit is a valid red commit for TDD.

    Args:
        repo_path: Path to the git repository
        commit_sha: SHA of the commit to check

    Returns:
        0 if the commit is a valid red commit, 1 if invalid, 2 if stub
    """
    raise NotImplementedError("tdd_check not yet implemented")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: tdd_check <repo_path> <commit_sha>", file=sys.stderr)
        sys.exit(2)

    repo_path = sys.argv[1]
    commit_sha = sys.argv[2]

    try:
        exit_code = check_red_commit(repo_path, commit_sha)
        sys.exit(exit_code)
    except NotImplementedError:
        sys.exit(2)
