"""Conformance test registry: maps requirement IDs to test node IDs."""

from typing import Dict, List


def build_coverage_report() -> Dict[str, List[str]]:
    """Build a coverage report mapping requirement IDs to test node IDs.

    Returns:
        A mapping of requirement identifier to a list of test node IDs that
        carry the checklist_id marker for that requirement.
    """
    # Stub: returns empty mapping. Implementation discovers test modules
    # under tests/conformance and extracts their checklist_id markers.
    return {}
