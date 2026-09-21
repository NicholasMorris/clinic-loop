"""AC5: Append-only violation detection."""

import tempfile
from pathlib import Path

import pytest

from clinicloop.evals.core.artifacts import AppendOnlyViolation, CaseArtifact, write_case


@pytest.mark.checklist_id("E2")
def test_overwriting_existing_case_file_raises() -> None:
    """Test that writing to an existing case file raises AppendOnlyViolation."""
    artifact = CaseArtifact(
        case_id="case_1",
        component="test_component",
        tree_hash="abc123",
        seed=42,
        outputs={"result": 0.95},
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        artifact_path = Path(tmpdir) / "case_1.json"

        # Write the first artifact (should succeed)
        write_case(artifact_path, artifact)
        assert artifact_path.exists()

        # Try to write to the same path again (should raise AppendOnlyViolation)
        with pytest.raises(AppendOnlyViolation):
            write_case(artifact_path, artifact)
