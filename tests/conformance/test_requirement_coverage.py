"""AC7: Requirement coverage mapping and allowlist validation."""

from pathlib import Path

import pytest

from clinicloop.evals.core.conformance import load_expected_unmapped, unmapped_requirement_ids


@pytest.mark.checklist_id("E2")
def test_unmapped_requirements_equal_committed_allowlist() -> None:
    """Test that unmapped requirements match the committed allowlist exactly."""
    checklist_path = Path(__file__).parent.parent.parent / "docs" / "brief-checklist.md"
    expected_unmapped_path = Path(__file__).parent / "expected_unmapped.txt"

    # For red commit: unmapped_requirement_ids() raises NotImplementedError
    # The actual test will:
    # 1. Parse checklist_path and extract all requirement IDs
    # 2. Find tests marked with @pytest.mark.checklist_id("<ID>")
    # 3. Return the set of unmapped IDs
    # 4. Load the allowlist from expected_unmapped_path
    # 5. Assert that unmapped == expected_unmapped (both sets equal)

    with pytest.raises(NotImplementedError):
        unmapped_requirement_ids(checklist_path)
