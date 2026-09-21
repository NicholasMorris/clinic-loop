"""Requirement coverage mapping via checklist markers."""

from pathlib import Path


def unmapped_requirement_ids(checklist_path: Path) -> set[str]:
    """Parse checklist file and return requirement IDs with no mapped test.

    Parses every identifier from the checklist file and returns those with
    no collected test node carrying the matching `checklist_id` marker.

    Args:
        checklist_path: Path to the docs/brief-checklist.md file.

    Returns:
        A set of unmapped requirement identifiers.
    """
    raise NotImplementedError


def load_expected_unmapped(expected_unmapped_path: Path) -> set[str]:
    """Load expected unmapped identifiers from the allowlist file.

    Args:
        expected_unmapped_path: Path to tests/conformance/expected_unmapped.txt.

    Returns:
        A set of expected unmapped identifiers.
    """
    raise NotImplementedError
