"""Scanner for forbidden names and I6 words in repository content.

This module scans tracked files, commit messages, and other content for:
- Hashed names from the denylist (R7 rule)
- I6 words (fraud, drug seeker, abuse) that should never be used

The denylist is stored as SHA-256 hashes to avoid committing forbidden names.
I6 words live in a single tracked file (i6_words.txt) with deliberate exception.
"""

from pathlib import Path
from typing import Set


def load_denylist(hash_file_path: Path) -> Set[str]:
    """Load the set of forbidden name hashes from a file.

    Args:
        hash_file_path: Path to the file containing SHA-256 hashes, one per line.

    Returns:
        Set of lowercase 64-character hash strings.

    Raises:
        SystemExit: If the file is missing or empty (exit code 2).
    """
    raise NotImplementedError


def scan_tree(
    tree_root: Path,
    denylist: Set[str],
    i6_words: Set[str],
) -> list[tuple[str, int, str]]:
    """Scan tracked files for forbidden names and I6 words.

    Args:
        tree_root: Root path of the repository.
        denylist: Set of forbidden name hashes.
        i6_words: Set of I6 words to match (whole word, case-insensitive).

    Returns:
        List of tuples (file_path, line_number, rule_id) for each hit.
    """
    raise NotImplementedError


def scan_payload(
    content: str,
    denylist: Set[str],
    i6_words: Set[str],
) -> list[tuple[int, str]]:
    """Scan commit message or PR/issue text payload for forbidden names and I6 words.

    Args:
        content: Text content (commit message, PR body, etc.).
        denylist: Set of forbidden name hashes.
        i6_words: Set of I6 words to match (whole word, case-insensitive).

    Returns:
        List of tuples (line_number, rule_id) for each hit.
    """
    raise NotImplementedError
