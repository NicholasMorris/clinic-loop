"""AC7: Requirement coverage mapping and allowlist validation."""

from pathlib import Path

import pytest

from clinicloop.evals.core.conformance import load_expected_unmapped, unmapped_requirement_ids


@pytest.mark.checklist_id("E2")
def test_unmapped_requirements_equal_committed_allowlist() -> None:
    """Test that unmapped requirements match the committed allowlist exactly."""
    checklist_path = Path(__file__).parent.parent.parent / "docs" / "brief-checklist.md"
    expected_unmapped_path = Path(__file__).parent / "expected_unmapped.txt"

    # Get unmapped requirements from checklist and marker scan
    unmapped = unmapped_requirement_ids(checklist_path)

    # Load the committed allowlist
    expected_unmapped = load_expected_unmapped(expected_unmapped_path)

    # They should match exactly
    assert unmapped == expected_unmapped, (
        f"Mismatch between unmapped requirements and allowlist.\n"
        f"In checklist but not mapped: {unmapped - expected_unmapped}\n"
        f"In allowlist but not in checklist: {expected_unmapped - unmapped}"
    )
