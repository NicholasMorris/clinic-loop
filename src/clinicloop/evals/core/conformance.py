"""Requirement coverage mapping via checklist markers."""

import re
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
    # Lazy import to avoid circular dependency issues
    from tests.conformance.registry import (
        build_coverage_report as build_coverage_report,
    )

    # Read the checklist file
    checklist_text = checklist_path.read_text()

    # Extract all requirement IDs (pattern: ^- <ID> )
    # This matches lines like "- B1 " or "- C0 " at any indentation level
    id_pattern = r"^[\s]*-\s+([A-Z][0-9]+)\s+"
    requirement_ids = set(re.findall(id_pattern, checklist_text, re.MULTILINE))

    # Build coverage report from tests
    coverage_report = build_coverage_report()

    # Find unmapped IDs (those not in the coverage report)
    mapped_ids = set(coverage_report.keys())
    unmapped = requirement_ids - mapped_ids

    return unmapped


def load_expected_unmapped(expected_unmapped_path: Path) -> set[str]:
    """Load expected unmapped identifiers from the allowlist file.

    Args:
        expected_unmapped_path: Path to tests/conformance/expected_unmapped.txt.

    Returns:
        A set of expected unmapped identifiers.
    """
    if not expected_unmapped_path.exists():
        return set()

    content = expected_unmapped_path.read_text()
    unmapped = set()

    for line in content.split("\n"):
        # Strip whitespace and ignore comments
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Extract ID (first token on the line)
        parts = line.split()
        if parts:
            unmapped.add(parts[0])

    return unmapped
