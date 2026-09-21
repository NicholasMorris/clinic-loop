"""Per-case artifact schema and tree hash computation."""

import hashlib
import json
import subprocess
from pathlib import Path

from pydantic import BaseModel


class CaseArtifact(BaseModel):
    """Pydantic schema for a per-case evaluation artifact.

    Attributes:
        case_id: Unique identifier for this case.
        component: The component being evaluated.
        tree_hash: SHA256 hash of eval-relevant paths.
        seed: The random seed used for this case.
        outputs: The outputs from this case.
    """

    case_id: str
    component: str
    tree_hash: str
    seed: int
    outputs: dict[str, object]


class AppendOnlyViolation(Exception):
    """Raised when attempting to overwrite an existing case file."""

    pass


def write_case(path: Path, artifact: CaseArtifact) -> None:
    """Write a case artifact to a file.

    Args:
        path: The file path to write to.
        artifact: The artifact to write.

    Raises:
        AppendOnlyViolation: If the file already exists.
    """
    if path.exists():
        raise AppendOnlyViolation(f"Case file already exists: {path}")

    # Create parent directory if needed
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write as JSON
    with open(path, "w") as f:
        json.dump(artifact.model_dump(), f, indent=2)


def compute_tree_hash(paths_file: Path, repo_dir: Path | None = None) -> str:
    """Compute the tree hash from eval-relevant paths.

    The tree hash is the SHA256 over the newline-joined sorted lines
    of "<path> <git rev-parse HEAD:<path>>" for the paths listed in
    the paths file.

    Args:
        paths_file: Path to the eval-relevant-paths.txt file.
        repo_dir: The git repository directory. If None, uses the parent of paths_file.

    Returns:
        The SHA256 hex digest of the tree hash.
    """
    if repo_dir is None:
        # Try parent directory of paths_file if it exists
        if paths_file.exists():
            repo_dir = paths_file.parent
        else:
            repo_dir = Path.cwd()

    # Read the list of relevant paths
    paths_text = paths_file.read_text().strip()
    paths = [p.strip() for p in paths_text.split("\n") if p.strip()]

    lines = []
    for path in sorted(paths):
        # Get the blob SHA for this path at HEAD
        result = subprocess.run(
            ["git", "rev-parse", f"HEAD:{path}"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            # Path doesn't exist in HEAD, skip it
            continue
        blob_sha = result.stdout.strip()
        lines.append(f"{path} {blob_sha}")

    # Sort and join
    lines.sort()
    tree_content = "\n".join(lines)

    # Compute SHA256
    return hashlib.sha256(tree_content.encode()).hexdigest()
