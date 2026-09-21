#!/usr/bin/env python3
"""Check for overlapping file ownership between GitHub issues.

Reads a JSON array of issue records from stdin and verifies that no two
issues have overlapping file glob patterns. Special rule: within the checks/
directory, per-file ownership is treated as disjoint (checks/a.sh and
checks/b.sh do not conflict), but checks/** conflicts with all checks/ files.

Exit codes:
- 0: All issues have disjoint file ownership
- 1: Two or more issues have overlapping globs
- 2: Stub implementation (not yet implemented)

Input format (JSON):
[
    {"key": "M0-1", "files": ["src/clinicloop/world/**", "tests/..."]},
    {"key": "M0-2", "files": ["src/clinicloop/api/**"]},
    ...
]

Output format:
On error (exit 1), prints the conflicting issue keys and the overlapping glob pattern.
"""

import json
import sys


def _glob_patterns_intersect(glob1: str, glob2: str) -> bool:
    """Check if two glob patterns intersect.

    Args:
        glob1: First glob pattern
        glob2: Second glob pattern

    Returns:
        True if the patterns can match the same file path.
    """
    # Handle special case: checks/ directory has per-file ownership
    if glob1.startswith("checks/") and glob2.startswith("checks/"):
        # Both are in checks/
        # checks/** conflicts with everything
        if glob1 == "checks/**" or glob2 == "checks/**":
            return True
        # checks/a.sh and checks/b.sh are disjoint
        if glob1 != "checks/**" and glob2 != "checks/**":
            return False

    # Check if glob1 matches any file that glob2 could match
    # We use a heuristic: check if patterns have common prefix
    # and whether wildcards would cause overlap

    # Remove ** and * to get the path prefix
    prefix1 = glob1.replace("**", "").replace("*", "").rstrip("/")
    prefix2 = glob2.replace("**", "").replace("*", "").rstrip("/")

    # If one glob is a prefix of the other, they intersect
    if prefix1 and prefix2:
        if prefix1.startswith(prefix2) or prefix2.startswith(prefix1):
            return True

    # Check using fnmatch-style matching
    # If glob1 has ** it matches anything under that path
    if "/**" in glob1:
        base1 = glob1.split("/**")[0]
        if glob2.startswith(base1):
            return True

    if "/**" in glob2:
        base2 = glob2.split("/**")[0]
        if glob1.startswith(base2):
            return True

    # Check if glob2 matches a typical file under glob1
    if glob1.endswith("/**"):
        base1 = glob1[:-3]  # Remove /**
        if glob2.startswith(base1):
            return True

    if glob2.endswith("/**"):
        base2 = glob2[:-3]
        if glob1.startswith(base2):
            return True

    return False


def check_glob_intersections(issues: list[dict]) -> int:
    """Check that no two issues have overlapping file globs.

    Args:
        issues: List of issue records with 'key' and 'files' fields

    Returns:
        0 if no overlapping globs, 1 if conflicts found, 2 if stub
    """
    # Check each pair of issues
    for i, issue1 in enumerate(issues):
        for issue2 in issues[i + 1 :]:
            # Check if any file glob from issue1 intersects with any from issue2
            for glob1 in issue1.get("files", []):
                for glob2 in issue2.get("files", []):
                    if _glob_patterns_intersect(glob1, glob2):
                        # Found intersection
                        print(
                            f"Conflict between {issue1['key']} and {issue2['key']}: "
                            f"overlapping glob patterns",
                            file=sys.stdout,
                        )
                        return 1

    return 0


if __name__ == "__main__":
    try:
        issues = json.load(sys.stdin)
        exit_code = check_glob_intersections(issues)
        sys.exit(exit_code)
    except NotImplementedError:
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
