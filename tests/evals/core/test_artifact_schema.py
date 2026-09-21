"""AC2: Artifact schema, unique case IDs, and tree hash computation."""

import tempfile
from pathlib import Path
from subprocess import run

import pytest
from pydantic import ValidationError

from clinicloop.evals.core.artifacts import (
    AppendOnlyViolation,
    CaseArtifact,
    compute_tree_hash,
    write_case,
)


@pytest.mark.checklist_id("E2")
def test_artifact_requires_core_fields_unique_case_ids_and_path_scoped_tree_hash() -> None:
    """Test artifact schema validation, uniqueness, and tree hash computation."""
    # Test 1: Missing case_id should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        CaseArtifact(  # type: ignore[call-arg]
            component="test_component",
            tree_hash="abc123",
            seed=42,
            outputs={"result": 0.95},
        )
    assert "case_id" in str(exc_info.value).lower()

    # Test 2: Missing component should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        CaseArtifact(  # type: ignore[call-arg]
            case_id="case_1",
            tree_hash="abc123",
            seed=42,
            outputs={"result": 0.95},
        )
    assert "component" in str(exc_info.value).lower()

    # Test 3: Missing tree_hash should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        CaseArtifact(  # type: ignore[call-arg]
            case_id="case_1",
            component="test_component",
            seed=42,
            outputs={"result": 0.95},
        )
    assert "tree_hash" in str(exc_info.value).lower()

    # Test 4: Missing seed should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        CaseArtifact(  # type: ignore[call-arg]
            case_id="case_1",
            component="test_component",
            tree_hash="abc123",
            outputs={"result": 0.95},
        )
    assert "seed" in str(exc_info.value).lower()

    # Test 5: Missing outputs should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        CaseArtifact(  # type: ignore[call-arg]
            case_id="case_1",
            component="test_component",
            tree_hash="abc123",
            seed=42,
        )
    assert "outputs" in str(exc_info.value).lower()

    # Test 6: Valid artifact creation
    artifact = CaseArtifact(
        case_id="case_1",
        component="test_component",
        tree_hash="abc123",
        seed=42,
        outputs={"result": 0.95},
    )
    assert artifact.case_id == "case_1"

    # Test 7: write_case should reject overwriting existing file
    with tempfile.TemporaryDirectory() as tmpdir:
        artifact_path = Path(tmpdir) / "case_1.json"
        # Write the first artifact (should succeed)
        write_case(artifact_path, artifact)
        assert artifact_path.exists()

        # Try to write to the same path again (should raise AppendOnlyViolation)
        with pytest.raises(AppendOnlyViolation):
            write_case(artifact_path, artifact)

    # Test 8: compute_tree_hash over a fixture repository
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir)

        # Initialize git repo
        run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
        run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

        # Create test files
        (repo_dir / "path1.txt").write_text("content1")
        (repo_dir / "path2.txt").write_text("content2")
        run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
        run(
            ["git", "commit", "-m", "initial"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

        # Create eval-relevant-paths.txt
        paths_file = repo_dir / "eval-relevant-paths.txt"
        paths_file.write_text("path1.txt\npath2.txt\n")

        # Compute tree hash
        hash1 = compute_tree_hash(paths_file)
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 hex is 64 chars

        # Modify one listed path
        (repo_dir / "path1.txt").write_text("modified content")
        run(
            ["git", "add", "path1.txt"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        run(
            ["git", "commit", "-m", "modify path1"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

        # Tree hash should change
        hash2 = compute_tree_hash(paths_file)
        assert hash2 != hash1

        # Modify an unlisted path
        (repo_dir / "other.txt").write_text("untracked content")
        run(
            ["git", "add", "other.txt"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        run(
            ["git", "commit", "-m", "add other"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

        # Tree hash should stay the same (other.txt is not in paths)
        hash3 = compute_tree_hash(paths_file)
        assert hash3 == hash2
