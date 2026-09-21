"""Per-case artifact schema and tree hash computation."""

from pathlib import Path
from pydantic import BaseModel, Field


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
    outputs: dict


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
    raise NotImplementedError


def compute_tree_hash(paths_file: Path) -> str:
    """Compute the tree hash from eval-relevant paths.

    The tree hash is the SHA256 over the newline-joined sorted lines
    of "<path> <git rev-parse HEAD:<path>>" for the paths listed in
    the paths file.

    Args:
        paths_file: Path to the eval-relevant-paths.txt file.

    Returns:
        The SHA256 hex digest of the tree hash.
    """
    raise NotImplementedError
