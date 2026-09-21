"""Git file reader for use in evals."""

import subprocess


def git_show(revision: str, path: str) -> str | None:
    """Read a file from a git revision via git show.

    Args:
        revision: Git revision (e.g., 'origin/main', 'HEAD').
        path: Path to file in the repository.

    Returns:
        File contents as string, or None if revision or path doesn't exist.
    """
    result = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return None

    return result.stdout
