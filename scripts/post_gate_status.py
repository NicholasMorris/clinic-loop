#!/usr/bin/env python3
"""Post a single commit-status context after local CI passes.

Posts the 'local-ci' status context to indicate that the local gate (make ci)
has completed successfully. This script is called by the orchestrator after
verifying the gate passes in a clean worktree at the head SHA.

The script reads GitHub API credentials and state from environment or arguments
and does not hold them internally (credentials passed by orchestrator, not
discovered by the subagent).

Exit codes:
- 0: Status posted successfully
- 1: Error posting status
- 2: Stub implementation (not yet implemented)
"""

import sys


def post_local_ci_status() -> int:
    """Post the local-ci status context.

    Returns:
        0 on success, 1 on error, 2 if stub
    """
    raise NotImplementedError("post_gate_status not yet implemented")


if __name__ == "__main__":
    try:
        exit_code = post_local_ci_status()
        sys.exit(exit_code)
    except NotImplementedError:
        sys.exit(2)
