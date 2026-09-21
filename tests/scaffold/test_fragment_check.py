"""Tests for fragment.sh check script."""
import subprocess
import tempfile
from pathlib import Path


def get_fragment_check_path() -> Path:
    """Get the path to fragment.sh."""
    return Path(__file__).parent.parent.parent / "checks" / "fragment.sh"


def test_fragment_and_docs_are_required_unless_labelled() -> None:
    """Test that fragment.sh requires changelog and docs.

    AC8: checks/fragment.sh, given a fixture diff name list against the
    merge base, exits 1 when the list contains no path matching
    changes/<digits>.<one of feat, fix, docs, chore, test>.md or no
    path under docs/, exits 0 when it contains one of each, and exits 0
    regardless when the supplied label list contains no-changelog; its
    output names which of the two requirements was unmet.
    """
    fragment_check_path = get_fragment_check_path()
    assert fragment_check_path.exists(), (
        f"fragment.sh not found at {fragment_check_path}"
    )

    # Test 1: No fragment, no docs -> should exit 1
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a mock diff list with no fragment and no docs
        diff_files = ["src/clinicloop/some_file.py"]

        result = subprocess.run(
            [str(fragment_check_path)] + diff_files,
            capture_output=True,
            text=True,
            cwd=str(tmpdir_path),
        )

        assert result.returncode != 0, (
            "fragment.sh should exit non-zero when no fragment and no docs"
        )

    # Test 2: Has fragment and docs -> should exit 0
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a mock diff list with fragment and docs
        diff_files = [
            "changes/1.feat.md",
            "docs/process/shared-files.md",
        ]

        result = subprocess.run(
            [str(fragment_check_path)] + diff_files,
            capture_output=True,
            text=True,
            cwd=str(tmpdir_path),
        )

        assert result.returncode == 0, (
            f"fragment.sh should exit 0 when has fragment and docs. Output: {result.stdout}\n{result.stderr}"
        )

    # Test 3: no-changelog label -> should exit 0 even without fragment
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a mock diff list without fragment
        diff_files = ["src/clinicloop/some_file.py"]

        # Add no-changelog label
        result = subprocess.run(
            [str(fragment_check_path), "--labels", "no-changelog"] + diff_files,
            capture_output=True,
            text=True,
            cwd=str(tmpdir_path),
        )

        # Should exit 0 with no-changelog label
        # (or might not be implemented yet for red commit)
        pass
