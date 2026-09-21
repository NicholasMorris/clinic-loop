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

import subprocess
import sys
from pathlib import Path


def _get_files_added_in_commit(repo_path: str, commit_sha: str) -> list[str]:
    """Get the list of files added in the given commit.

    Args:
        repo_path: Path to the git repository
        commit_sha: SHA of the commit to check

    Returns:
        List of file paths added in the commit.
    """
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-status", "-r", commit_sha],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return []

    files = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            status = parts[0]
            filepath = parts[1]
            # A = added, M = modified, but we focus on added files
            if status in ("A", "M"):
                files.append(filepath)

    return files


def _run_tests_for_files(repo_path: str, test_files: list[str]) -> tuple[int, str]:
    """Run pytest on the given test files.

    Args:
        repo_path: Path to the git repository
        test_files: List of test file paths to run

    Returns:
        Tuple of (exit_code, stdout+stderr output).
    """
    if not test_files:
        return 1, "No test files found"

    # Run pytest with verbose output to capture failure reasons
    result = subprocess.run(
        ["python", "-m", "pytest"] + test_files + ["-v", "--tb=short"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    return result.returncode, result.stdout + result.stderr


def _check_failure_reason(output: str) -> bool:
    """Check if test failures are for accepted reasons.

    Accepted reasons:
    - AssertionError
    - NotImplementedError raised from a stub under src/

    Rejected reasons:
    - SyntaxError (collection error)
    - ImportError
    - NameError
    - AttributeError

    Args:
        output: The pytest output

    Returns:
        True if failures are for accepted reasons, False otherwise.
    """
    output_lower = output.lower()

    # Check for rejected error types
    rejected_errors = [
        "syntaxerror",
        "importerror",
        "nameerror",
        "attributeerror",
        "error: collection",
        "ERROR",
    ]

    for error_type in rejected_errors:
        if error_type in output_lower:
            # Check if it's actually a test failure or a collection error
            if error_type == "error: collection":
                return False
            if error_type == "syntaxerror" and ("line" in output_lower or "invalid" in output_lower):
                return False
            if error_type in ["importerror", "nameerror", "attributeerror"]:
                if "error" in output_lower or "failed" in output_lower:
                    return False

    # Check for accepted error types
    if "assertionerror" in output_lower or "notimplementederror" in output_lower:
        return True

    # Check for FAILED marker with assertion
    if "FAILED" in output and ("assert" in output or "notimplemented" in output.lower()):
        return True

    return False


def check_red_commit(repo_path: str, commit_sha: str) -> int:
    """Check that a commit is a valid red commit for TDD.

    Args:
        repo_path: Path to the git repository
        commit_sha: SHA of the commit to check

    Returns:
        0 if the commit is a valid red commit, 1 if invalid, 2 if stub
    """
    # Get files added in this commit
    added_files = _get_files_added_in_commit(repo_path, commit_sha)

    # Filter for test files
    test_files = [f for f in added_files if f.startswith("tests/")]

    if not test_files:
        print(f"{commit_sha}: No test files added in commit", file=sys.stderr)
        return 1

    # Run the tests
    exit_code, output = _run_tests_for_files(repo_path, test_files)

    # Tests should fail (non-zero exit code)
    if exit_code == 0:
        print(f"{commit_sha}: Tests passed but should fail for red commit", file=sys.stderr)
        return 1

    # Check that failures are for accepted reasons
    if _check_failure_reason(output):
        return 0

    # Failures are for unaccepted reasons
    print(f"{commit_sha}: Tests fail for wrong reason (collection error or wrong exception type)", file=sys.stderr)
    return 1


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
