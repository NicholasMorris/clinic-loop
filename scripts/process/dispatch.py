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


def check_glob_intersections(issues: list[dict]) -> int:
    """Check that no two issues have overlapping file globs.

    Args:
        issues: List of issue records with 'key' and 'files' fields

    Returns:
        0 if no overlapping globs, 1 if conflicts found, 2 if stub
    """
    raise NotImplementedError("dispatch not yet implemented")


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
