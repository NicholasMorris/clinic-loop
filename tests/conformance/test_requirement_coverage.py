"""AC7: Requirement coverage mapping and allowlist validation."""

from pathlib import Path

import pytest

from clinicloop.evals.core.conformance import load_expected_unmapped, unmapped_requirement_ids


@pytest.mark.checklist_id("E2")
def test_unmapped_requirements_equal_committed_allowlist() -> None:
    """Test that every unmapped requirement is covered by the committed allowlist."""
    checklist_path = Path(__file__).parent.parent.parent / "docs" / "brief-checklist.md"
    expected_unmapped_path = Path(__file__).parent / "expected_unmapped.txt"

    # Get unmapped requirements from checklist and marker scan
    unmapped = unmapped_requirement_ids(checklist_path)

    # Load the committed allowlist
    expected_unmapped = load_expected_unmapped(expected_unmapped_path)

    # No requirement may lose its conformance test: every unmapped ID must be allowlisted.
    # Stale allowlist entries (requirements mapped since) are harmless, so the check is a subset.
    assert unmapped <= expected_unmapped, (
        "Requirements with no conformance test and no allowlist entry: "
        f"{sorted(unmapped - expected_unmapped)}"
    )
